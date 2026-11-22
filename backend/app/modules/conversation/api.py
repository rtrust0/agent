from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.conversation.schema import (
    ConversationAnnotate,
    ConversationRead,
    ConversationTurnRead,
)
from app.modules.conversation.service import ConversationService
from app.modules.user.model import User

router = APIRouter(prefix="/conversations", tags=["对话日志"])
trace_router = APIRouter(tags=["对话日志"])


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


@router.get(
    "", response_model=ResponseSchema[PageResult[ConversationRead]], summary="对话列表"
)
async def list_conversations(
    params: PageParams = Depends(),
    status: str | None = Query(None),
    agent_id: int | None = Query(None),
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:list")),
) -> ResponseSchema[PageResult[ConversationRead]]:
    rows, total = await svc.list_conversations(
        params, current_user, status=status, agent_id=agent_id
    )
    return ResponseSchema(
        data=PageResult(
            items=[ConversationRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.get(
    "/{conversation_id}",
    response_model=ResponseSchema[ConversationRead],
    summary="对话详情",
)
async def get_conversation(
    conversation_id: int,
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:read")),
) -> ResponseSchema[ConversationRead]:
    conversation = await svc.get_conversation(conversation_id, current_user)
    return ResponseSchema(data=ConversationRead.model_validate(conversation))


@router.get(
    "/{conversation_id}/turns",
    response_model=ResponseSchema[list[ConversationTurnRead]],
    summary="对话轮次",
)
async def list_turns(
    conversation_id: int,
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:read")),
) -> ResponseSchema[list[ConversationTurnRead]]:
    turns = await svc.list_turns(conversation_id, current_user)
    return ResponseSchema(data=[ConversationTurnRead.model_validate(t) for t in turns])


@router.post(
    "/{conversation_id}/annotate",
    response_model=ResponseSchema[ConversationRead],
    summary="对话标注",
)
async def annotate_conversation(
    conversation_id: int,
    data: ConversationAnnotate,
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:annotate")),
) -> ResponseSchema[ConversationRead]:
    conversation = await svc.annotate(current_user, conversation_id, data)
    return ResponseSchema(data=ConversationRead.model_validate(conversation))


@router.get("/{conversation_id}/export", summary="对话导出（CSV）")
async def export_conversation(
    conversation_id: int,
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:export")),
) -> Response:
    content = await svc.export_csv(current_user, conversation_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="conversation-{conversation_id}.csv"'
        },
    )


@trace_router.get(
    "/turns/{turn_id}/trace",
    response_model=ResponseSchema[ConversationTurnRead],
    summary="对话轮次链路追踪",
)
async def get_turn_trace(
    turn_id: int,
    svc: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user_with_permission("conversation:read")),
) -> ResponseSchema[ConversationTurnRead]:
    turn = await svc.get_turn_trace(turn_id, current_user)
    return ResponseSchema(data=ConversationTurnRead.model_validate(turn))
