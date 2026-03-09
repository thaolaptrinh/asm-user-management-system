import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Item, session)

    async def get_by_owner(
        self, owner_id: uuid.UUID, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Item]:
        result = await self.session.execute(
            select(Item).where(Item.owner_id == owner_id).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
        )
        return result.scalar_one()
