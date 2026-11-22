from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.knowledge.schema import (
    DocumentRead,
    DocumentUpload,
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
    ReindexResult,
    RetrievalTestRequest,
    RetrievalTestResult,
    SegmentRead,
    SegmentUpdate,
)
from app.modules.knowledge.service import KnowledgeService
from app.modules.user.model import User

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])


def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


@router.get(
    "", response_model=ResponseSchema[PageResult[KnowledgeBaseRead]], summary="知识库列表"
)
async def list_knowledge_bases(
    params: PageParams = Depends(),
    status: str | None = Query(None),
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:list")),
) -> ResponseSchema[PageResult[KnowledgeBaseRead]]:
    rows, total = await svc.list_kbs(params, current_user, status=status)
    return ResponseSchema(
        data=PageResult(
            items=[KnowledgeBaseRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[KnowledgeBaseRead], summary="创建知识库")
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:create")),
) -> ResponseSchema[KnowledgeBaseRead]:
    kb = await svc.create(current_user, data)
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(kb))


@router.get(
    "/{kb_id}", response_model=ResponseSchema[KnowledgeBaseRead], summary="知识库详情"
)
async def get_knowledge_base(
    kb_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:read")),
) -> ResponseSchema[KnowledgeBaseRead]:
    kb = await svc.get_kb(kb_id, current_user)
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(kb))


@router.put(
    "/{kb_id}", response_model=ResponseSchema[KnowledgeBaseRead], summary="更新知识库配置"
)
async def update_knowledge_base(
    kb_id: int,
    data: KnowledgeBaseUpdate,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:update")),
) -> ResponseSchema[KnowledgeBaseRead]:
    kb = await svc.update(current_user, kb_id, data)
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(kb))


@router.delete("/{kb_id}", response_model=ResponseSchema[None], summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, kb_id)
    return ResponseSchema(data=None)


@router.get(
    "/{kb_id}/documents",
    response_model=ResponseSchema[PageResult[DocumentRead]],
    summary="文档列表",
)
async def list_documents(
    kb_id: int,
    params: PageParams = Depends(),
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:read")),
) -> ResponseSchema[PageResult[DocumentRead]]:
    rows, total = await svc.list_documents(kb_id, params, current_user)
    return ResponseSchema(
        data=PageResult(
            items=[DocumentRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post(
    "/{kb_id}/documents", response_model=ResponseSchema[DocumentRead], summary="上传文档"
)
async def upload_document(
    kb_id: int,
    data: DocumentUpload,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:document_upload")),
) -> ResponseSchema[DocumentRead]:
    document = await svc.upload_document(current_user, kb_id, data)
    return ResponseSchema(data=DocumentRead.model_validate(document))


@router.post(
    "/{kb_id}/documents/{doc_id}/retry",
    response_model=ResponseSchema[DocumentRead],
    summary="重试文档处理",
)
async def retry_document(
    kb_id: int,
    doc_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:document_upload")),
) -> ResponseSchema[DocumentRead]:
    document = await svc.retry_document(current_user, kb_id, doc_id)
    return ResponseSchema(data=DocumentRead.model_validate(document))


@router.delete(
    "/{kb_id}/documents/{doc_id}",
    response_model=ResponseSchema[None],
    summary="删除文档",
)
async def delete_document(
    kb_id: int,
    doc_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:document_delete")),
) -> ResponseSchema[None]:
    await svc.delete_document(current_user, kb_id, doc_id)
    return ResponseSchema(data=None)


@router.get(
    "/{kb_id}/segments",
    response_model=ResponseSchema[PageResult[SegmentRead]],
    summary="分段列表",
)
async def list_segments(
    kb_id: int,
    params: PageParams = Depends(),
    document_id: int | None = Query(None),
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:read")),
) -> ResponseSchema[PageResult[SegmentRead]]:
    rows, total = await svc.list_segments(kb_id, params, current_user, document_id=document_id)
    return ResponseSchema(
        data=PageResult(
            items=[SegmentRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.put(
    "/{kb_id}/segments/{seg_id}",
    response_model=ResponseSchema[SegmentRead],
    summary="更新分段内容",
)
async def update_segment(
    kb_id: int,
    seg_id: int,
    data: SegmentUpdate,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:document_delete")),
) -> ResponseSchema[SegmentRead]:
    segment = await svc.update_segment(current_user, kb_id, seg_id, data)
    return ResponseSchema(data=SegmentRead.model_validate(segment))


@router.delete(
    "/{kb_id}/segments/{seg_id}",
    response_model=ResponseSchema[None],
    summary="删除分段",
)
async def delete_segment(
    kb_id: int,
    seg_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:document_delete")),
) -> ResponseSchema[None]:
    await svc.delete_segment(current_user, kb_id, seg_id)
    return ResponseSchema(data=None)


@router.post(
    "/{kb_id}/retrieval-test",
    response_model=ResponseSchema[RetrievalTestResult],
    summary="检索测试",
)
async def retrieval_test(
    kb_id: int,
    data: RetrievalTestRequest,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:retrieval_test")),
) -> ResponseSchema[RetrievalTestResult]:
    result = await svc.retrieval_test(kb_id, current_user, data.query, data.top_k)
    return ResponseSchema(data=result)


@router.post(
    "/{kb_id}/reindex", response_model=ResponseSchema[ReindexResult], summary="重新索引"
)
async def reindex(
    kb_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
    current_user: User = Depends(get_current_user_with_permission("knowledge:reindex")),
) -> ResponseSchema[ReindexResult]:
    result = await svc.reindex(current_user, kb_id)
    return ResponseSchema(data=result)
