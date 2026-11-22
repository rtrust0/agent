from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.knowledge.model import Document, KnowledgeBase, Segment


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    SEARCH_FIELDS = ["name", "description"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(KnowledgeBase, db)


class DocumentRepository(BaseRepository[Document]):
    SEARCH_FIELDS = ["file_name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Document, db)

    async def list_by_kb(self, kb_id: int, offset: int, limit: int) -> tuple[list[Document], int]:
        return await self.get_page(
            offset, limit, extra_conditions=[Document.knowledge_base_id == kb_id]
        )

    async def delete_by_kb(self, kb_id: int) -> None:
        await self.db.execute(delete(Document).where(Document.knowledge_base_id == kb_id))


class SegmentRepository(BaseRepository[Segment]):
    SEARCH_FIELDS = ["content"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Segment, db)

    async def list_by_kb(
        self, kb_id: int, offset: int, limit: int, document_id: int | None = None
    ) -> tuple[list[Segment], int]:
        conditions = [Segment.knowledge_base_id == kb_id]
        if document_id is not None:
            conditions.append(Segment.document_id == document_id)
        return await self.get_page(offset, limit, extra_conditions=conditions)

    async def list_for_retrieval(self, kb_id: int, limit: int = 500) -> list[Segment]:
        rows = await self.db.execute(
            select(Segment)
            .where(Segment.knowledge_base_id == kb_id)
            .order_by(Segment.position.asc())
            .limit(limit)
        )
        return list(rows.scalars().all())

    async def delete_by_document(self, document_id: int) -> None:
        await self.db.execute(delete(Segment).where(Segment.document_id == document_id))

    async def delete_by_kb(self, kb_id: int) -> None:
        await self.db.execute(delete(Segment).where(Segment.knowledge_base_id == kb_id))

    async def count_by_kb(self, kb_id: int) -> int:
        return (
            await self.db.execute(
                select(func.count()).select_from(Segment).where(Segment.knowledge_base_id == kb_id)
            )
        ).scalar_one()
