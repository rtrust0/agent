from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import assert_in_scope, scope_condition
from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.knowledge.model import Document, KnowledgeBase, Segment
from app.modules.knowledge.repository import (
    DocumentRepository,
    KnowledgeBaseRepository,
    SegmentRepository,
)
from app.modules.knowledge.schema import (
    DocumentUpload,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    ReindexResult,
    RetrievalHit,
    RetrievalTestResult,
    SegmentUpdate,
)
from app.modules.user.model import User

ALLOWED_FILE_TYPES = {"pdf", "docx", "md", "txt", "html", "csv"}


def split_content(content: str, chunk_size: int, overlap: int) -> list[str]:
    """按固定窗口切分文本，窗口间保留 overlap 字符重叠。"""
    step = max(chunk_size - overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(content), step):
        piece = content[start : start + chunk_size]
        if piece.strip():
            chunks.append(piece)
        if start + chunk_size >= len(content):
            break
    return chunks


class KnowledgeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.segment_repo = SegmentRepository(db)
        self.audit = AuditService(db)

    # ---------------- 知识库 ----------------
    async def list_kbs(
        self, params: PageParams, current_user: User, *, status: str | None = None
    ) -> tuple[list[KnowledgeBase], int]:
        conditions = []
        scope = scope_condition(KnowledgeBase, current_user)
        if scope is not None:
            conditions.append(scope)
        if status:
            conditions.append(KnowledgeBase.status == status)
        return await self.kb_repo.get_page(
            params.offset, params.page_size, params.keyword, extra_conditions=conditions or None
        )

    async def get_kb(self, kb_id: int, current_user: User) -> KnowledgeBase:
        kb = await self.kb_repo.get_by_id(kb_id)
        if not kb:
            raise BizException(code=404, message="知识库不存在")
        assert_in_scope(kb, current_user, message="没有权限访问该知识库")
        return kb

    async def create(self, actor: User, data: KnowledgeBaseCreate) -> KnowledgeBase:
        kb = KnowledgeBase(
            name=data.name.strip(),
            description=data.description,
            status="empty",
            embedding_model=data.embedding_model,
            chunk_method=data.chunk_method,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            retrieval_strategy=data.retrieval_strategy,
            top_k=data.top_k,
            similarity_threshold=data.similarity_threshold,
            created_by=actor.username,
        )
        self.db.add(kb)
        await self.db.flush()
        self.audit.record(
            actor,
            module="knowledge",
            action="create",
            target_id=kb.id,
            target_name=kb.name,
            detail={"chunk_size": kb.chunk_size, "retrieval_strategy": kb.retrieval_strategy},
        )
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def update(
        self, actor: User, kb_id: int, data: KnowledgeBaseUpdate
    ) -> KnowledgeBase:
        kb = await self.get_kb(kb_id, actor)
        before = {
            "name": kb.name,
            "chunk_size": kb.chunk_size,
            "top_k": kb.top_k,
            "similarity_threshold": kb.similarity_threshold,
        }
        for field in (
            "name",
            "description",
            "embedding_model",
            "chunk_method",
            "chunk_size",
            "chunk_overlap",
            "retrieval_strategy",
            "top_k",
            "similarity_threshold",
        ):
            value = getattr(data, field)
            if value is not None:
                setattr(kb, field, value)
        self.audit.record(
            actor,
            module="knowledge",
            action="update",
            target_id=kb.id,
            target_name=kb.name,
            detail={
                "before": before,
                "after": {
                    "name": kb.name,
                    "chunk_size": kb.chunk_size,
                    "top_k": kb.top_k,
                    "similarity_threshold": kb.similarity_threshold,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def delete(self, actor: User, kb_id: int) -> None:
        kb = await self.get_kb(kb_id, actor)
        await self.segment_repo.delete_by_kb(kb.id)
        await self.doc_repo.delete_by_kb(kb.id)
        self.audit.record(
            actor, module="knowledge", action="delete", target_id=kb.id, target_name=kb.name
        )
        await self.kb_repo.delete(kb)
        await self.db.commit()

    # ---------------- 文档 ----------------
    async def upload_document(
        self, actor: User, kb_id: int, data: DocumentUpload
    ) -> Document:
        kb = await self.get_kb(kb_id, actor)
        file_type = data.file_type.strip().lower().lstrip(".")
        if file_type not in ALLOWED_FILE_TYPES:
            raise BizException(code=400, message="不支持的文档类型")

        document = Document(
            knowledge_base_id=kb.id,
            file_name=data.file_name.strip(),
            file_type=file_type,
            file_size=data.file_size,
            minio_path=data.minio_path,
            status="processing",
            word_count=len(data.content),
            uploaded_by=actor.username,
        )
        self.db.add(document)
        await self.db.flush()

        chunks = split_content(data.content, kb.chunk_size, kb.chunk_overlap)
        for position, chunk in enumerate(chunks, start=1):
            self.db.add(
                Segment(
                    knowledge_base_id=kb.id,
                    document_id=document.id,
                    position=position,
                    content=chunk,
                    word_count=len(chunk),
                    token_count=len(chunk),
                )
            )

        document.status = "completed"
        document.segment_count = len(chunks)
        document.processed_at = datetime.now()
        kb.status = "ready"
        await self._refresh_counts(kb)
        self.audit.record(
            actor,
            module="knowledge",
            action="upload",
            target_id=document.id,
            target_name=document.file_name,
            detail={"knowledge_base_id": kb.id, "segment_count": len(chunks)},
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def list_documents(
        self, kb_id: int, params: PageParams, current_user: User
    ) -> tuple[list[Document], int]:
        kb = await self.get_kb(kb_id, current_user)
        return await self.doc_repo.list_by_kb(kb.id, params.offset, params.page_size)

    async def _get_document(self, kb_id: int, doc_id: int) -> Document:
        document = await self.doc_repo.get_by_id(doc_id)
        if not document or document.knowledge_base_id != kb_id:
            raise BizException(code=404, message="文档不存在")
        return document

    async def retry_document(self, actor: User, kb_id: int, doc_id: int) -> Document:
        kb = await self.get_kb(kb_id, actor)
        document = await self._get_document(kb.id, doc_id)
        document.status = "completed"
        document.error_message = None
        document.processed_at = datetime.now()
        kb.status = "ready"
        await self._refresh_counts(kb)
        self.audit.record(
            actor,
            module="knowledge",
            action="retry",
            target_id=document.id,
            target_name=document.file_name,
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_document(self, actor: User, kb_id: int, doc_id: int) -> None:
        kb = await self.get_kb(kb_id, actor)
        document = await self._get_document(kb.id, doc_id)
        await self.segment_repo.delete_by_document(document.id)
        self.audit.record(
            actor,
            module="knowledge",
            action="delete",
            target_id=document.id,
            target_name=document.file_name,
            detail={"knowledge_base_id": kb.id, "type": "document"},
        )
        await self.doc_repo.delete(document)
        await self._refresh_counts(kb)
        await self.db.commit()

    # ---------------- 分段 ----------------
    async def list_segments(
        self,
        kb_id: int,
        params: PageParams,
        current_user: User,
        *,
        document_id: int | None = None,
    ) -> tuple[list[Segment], int]:
        kb = await self.get_kb(kb_id, current_user)
        return await self.segment_repo.list_by_kb(
            kb.id, params.offset, params.page_size, document_id
        )

    async def _get_segment(self, kb_id: int, segment_id: int) -> Segment:
        segment = await self.segment_repo.get_by_id(segment_id)
        if not segment or segment.knowledge_base_id != kb_id:
            raise BizException(code=404, message="分段不存在")
        return segment

    async def update_segment(
        self, actor: User, kb_id: int, segment_id: int, data: SegmentUpdate
    ) -> Segment:
        kb = await self.get_kb(kb_id, actor)
        segment = await self._get_segment(kb.id, segment_id)
        segment.content = data.content
        segment.word_count = len(data.content)
        segment.token_count = len(data.content)
        self.audit.record(
            actor,
            module="knowledge",
            action="update",
            target_id=segment.id,
            target_name=f"分段 #{segment.position}",
            detail={"knowledge_base_id": kb.id, "type": "segment"},
        )
        await self.db.commit()
        await self.db.refresh(segment)
        return segment

    async def delete_segment(self, actor: User, kb_id: int, segment_id: int) -> None:
        kb = await self.get_kb(kb_id, actor)
        segment = await self._get_segment(kb.id, segment_id)
        await self.segment_repo.delete(segment)
        await self._refresh_counts(kb)
        self.audit.record(
            actor,
            module="knowledge",
            action="delete",
            target_id=segment_id,
            target_name=f"分段 #{segment.position}",
            detail={"knowledge_base_id": kb.id, "type": "segment"},
        )
        await self.db.commit()

    # ---------------- 检索 / 重建索引 ----------------
    async def retrieval_test(
        self, kb_id: int, current_user: User, query: str, top_k: int | None
    ) -> RetrievalTestResult:
        kb = await self.get_kb(kb_id, current_user)
        segments = await self.segment_repo.list_for_retrieval(kb.id)
        limit = top_k or kb.top_k
        tokens = [token for token in query.replace("，", " ").split() if token]
        if not tokens:
            tokens = [query]

        scored: list[tuple[float, Segment]] = []
        for segment in segments:
            matches = sum(segment.content.count(token) for token in tokens)
            if matches == 0:
                continue
            score = round(min(1.0, matches / len(tokens)), 4)
            if score < kb.similarity_threshold:
                continue
            scored.append((score, segment))

        scored.sort(key=lambda item: item[0], reverse=True)
        hits: list[RetrievalHit] = []
        for score, segment in scored[:limit]:
            segment.hit_count += 1
            hits.append(
                RetrievalHit(
                    segment_id=segment.id,
                    document_id=segment.document_id,
                    content=segment.content,
                    score=score,
                )
            )
        await self.db.commit()
        return RetrievalTestResult(knowledge_base_id=kb.id, query=query, hits=hits)

    async def reindex(self, actor: User, kb_id: int) -> ReindexResult:
        kb = await self.get_kb(kb_id, actor)
        await self._refresh_counts(kb)
        self.audit.record(
            actor,
            module="knowledge",
            action="reindex",
            target_id=kb.id,
            target_name=kb.name,
            detail={"document_count": kb.document_count, "segment_count": kb.segment_count},
        )
        await self.db.commit()
        return ReindexResult(
            knowledge_base_id=kb.id,
            document_count=kb.document_count,
            segment_count=kb.segment_count,
            status=kb.status,
        )

    async def _refresh_counts(self, kb: KnowledgeBase) -> None:
        kb.document_count = (
            await self.db.execute(
                select(func.count())
                .select_from(Document)
                .where(Document.knowledge_base_id == kb.id)
            )
        ).scalar_one()
        kb.segment_count = await self.segment_repo.count_by_kb(kb.id)
        kb.status = "ready" if kb.document_count else "empty"
