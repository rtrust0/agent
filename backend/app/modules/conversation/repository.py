from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.conversation.model import Conversation, ConversationTurn


class ConversationRepository(BaseRepository[Conversation]):
    SEARCH_FIELDS = ["agent_name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Conversation, db)


class ConversationTurnRepository(BaseRepository[ConversationTurn]):
    SEARCH_FIELDS = ["content"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ConversationTurn, db)

    async def list_by_conversation(self, conversation_id: int) -> list[ConversationTurn]:
        rows = await self.db.execute(
            select(ConversationTurn)
            .where(ConversationTurn.conversation_id == conversation_id)
            .order_by(ConversationTurn.position.asc())
        )
        return list(rows.scalars().all())
