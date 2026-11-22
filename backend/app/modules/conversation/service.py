import csv
import io

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import assert_in_scope, scope_condition
from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.conversation.model import Conversation, ConversationTurn
from app.modules.conversation.repository import (
    ConversationRepository,
    ConversationTurnRepository,
)
from app.modules.conversation.schema import ConversationAnnotate
from app.modules.user.model import User


class ConversationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ConversationRepository(db)
        self.turn_repo = ConversationTurnRepository(db)
        self.audit = AuditService(db)

    async def list_conversations(
        self,
        params: PageParams,
        current_user: User,
        *,
        status: str | None = None,
        agent_id: int | None = None,
    ) -> tuple[list[Conversation], int]:
        conditions = []
        scope = scope_condition(
            Conversation, current_user, owner_field="user_id", owner_is_user_id=True
        )
        if scope is not None:
            conditions.append(scope)
        if status:
            conditions.append(Conversation.status == status)
        if agent_id is not None:
            conditions.append(Conversation.agent_id == agent_id)
        return await self.repo.get_page(
            params.offset,
            params.page_size,
            params.keyword,
            extra_conditions=conditions or None,
            order_desc=True,
        )

    async def get_conversation(self, conversation_id: int, current_user: User) -> Conversation:
        conversation = await self.repo.get_by_id(conversation_id)
        if not conversation:
            raise BizException(code=404, message="对话不存在")
        assert_in_scope(
            conversation,
            current_user,
            owner_field="user_id",
            owner_is_user_id=True,
            message="没有权限访问该对话",
        )
        return conversation

    async def list_turns(
        self, conversation_id: int, current_user: User
    ) -> list[ConversationTurn]:
        conversation = await self.get_conversation(conversation_id, current_user)
        return await self.turn_repo.list_by_conversation(conversation.id)

    async def get_turn_trace(self, turn_id: int, current_user: User) -> ConversationTurn:
        turn = await self.turn_repo.get_by_id(turn_id)
        if not turn:
            raise BizException(code=404, message="对话轮次不存在")
        await self.get_conversation(turn.conversation_id, current_user)
        return turn

    async def annotate(
        self, actor: User, conversation_id: int, data: ConversationAnnotate
    ) -> Conversation:
        conversation = await self.get_conversation(conversation_id, actor)
        before = {
            "rating": conversation.rating,
            "tags": conversation.tags,
            "needs_optimization": conversation.needs_optimization,
        }
        if data.rating is not None:
            conversation.rating = data.rating
        if data.tags is not None:
            conversation.tags = data.tags
        if data.needs_optimization is not None:
            conversation.needs_optimization = data.needs_optimization
        if data.annotation is not None:
            conversation.annotation = data.annotation
        if data.satisfaction is not None:
            conversation.satisfaction = data.satisfaction
        self.audit.record(
            actor,
            module="conversation",
            action="annotate",
            target_id=conversation.id,
            target_name=conversation.agent_name,
            detail={
                "before": before,
                "after": {
                    "rating": conversation.rating,
                    "tags": conversation.tags,
                    "needs_optimization": conversation.needs_optimization,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def export_csv(self, actor: User, conversation_id: int) -> str:
        conversation = await self.get_conversation(conversation_id, actor)
        turns = await self.turn_repo.list_by_conversation(conversation.id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["conversation_id", "position", "role", "content", "timestamp"])
        for turn in turns:
            writer.writerow(
                [
                    conversation.id,
                    turn.position,
                    turn.role,
                    turn.content,
                    turn.timestamp.isoformat(sep=" ") if turn.timestamp else "",
                ]
            )
        self.audit.record(
            actor,
            module="conversation",
            action="export",
            target_id=conversation.id,
            target_name=conversation.agent_name,
            detail={"turns": len(turns)},
        )
        await self.db.commit()
        return buffer.getvalue()
