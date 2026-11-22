from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """通用数据访问层：CRUD + 分页搜索。"""

    SEARCH_FIELDS: list[str] = ["name"]

    def __init__(self, model: Type[T], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, obj_id: int) -> T | None:
        return await self.db.get(self.model, obj_id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        await self.db.delete(obj)
        await self.db.flush()

    async def delete_by_id(self, obj_id: int) -> None:
        await self.db.execute(delete(self.model).where(self.model.id == obj_id))

    async def get_page(
        self,
        offset: int = 0,
        limit: int = 10,
        keyword: str | None = None,
        search_fields: list[str] | None = None,
        extra_conditions: list | None = None,
        order_desc: bool = False,
    ) -> tuple[list[T], int]:
        stmt = select(self.model)
        if extra_conditions:
            stmt = stmt.where(*extra_conditions)
        fields = search_fields or self.SEARCH_FIELDS
        if keyword and fields:
            conditions = [
                getattr(self.model, name).like(f"%{keyword}%")
                for name in fields
                if hasattr(self.model, name)
            ]
            if conditions:
                stmt = stmt.where(or_(*conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        order = self.model.id.desc() if order_desc else self.model.id.asc()
        stmt = stmt.offset(offset).limit(limit).order_by(order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
