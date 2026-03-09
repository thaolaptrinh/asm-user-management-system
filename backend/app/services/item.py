import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.item import Item
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, item_repo: ItemRepository) -> None:
        self._repo = item_repo

    async def create(self, owner_id: uuid.UUID, data: ItemCreate) -> Item:
        return await self._repo.create(
            title=data.title,
            description=data.description,
            owner_id=owner_id,
        )

    async def update(self, item: Item, data: ItemUpdate) -> Item:
        update_kwargs = data.model_dump(exclude_unset=True)
        return await self._repo.update(item, **update_kwargs)

    async def get_or_404(self, item_id: uuid.UUID, owner_id: uuid.UUID) -> Item:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise NotFoundError("Item", item_id)
        if item.owner_id != owner_id:
            raise ForbiddenError("You don't have permission to access this item")
        return item

    async def delete(self, item: Item) -> None:
        await self._repo.delete(item)

    async def get_by_owner(
        self, owner_id: uuid.UUID, *, skip: int = 0, limit: int = 100
    ):
        return await self._repo.get_by_owner(owner_id, skip=skip, limit=limit)

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        return await self._repo.count_by_owner(owner_id)
