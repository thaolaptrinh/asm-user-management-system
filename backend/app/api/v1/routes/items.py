import uuid

from fastapi import APIRouter

from app.api.v1.deps import CurrentUser, ItemServiceDep, SuperuserDep
from app.schemas.common import Message, PaginatedResponse
from app.schemas.item import ItemCreate, ItemPublic, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=PaginatedResponse[ItemPublic], operation_id="listItems")
async def list_items(
    current_user: CurrentUser,
    item_service: ItemServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> PaginatedResponse[ItemPublic]:
    items = await item_service.get_by_owner(current_user.id, skip=skip, limit=limit)
    count = await item_service.count_by_owner(current_user.id)
    return PaginatedResponse(
        data=[ItemPublic.model_validate(i) for i in items],
        count=count,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=ItemPublic, status_code=201, operation_id="createItem")
async def create_item(
    data: ItemCreate,
    current_user: CurrentUser,
    item_service: ItemServiceDep,
) -> ItemPublic:
    item = await item_service.create(current_user.id, data)
    return ItemPublic.model_validate(item)


@router.get("/{item_id}", response_model=ItemPublic, operation_id="getItem")
async def get_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    item_service: ItemServiceDep,
) -> ItemPublic:
    item = await item_service.get_or_404(item_id, current_user.id)
    return ItemPublic.model_validate(item)


@router.patch("/{item_id}", response_model=ItemPublic, operation_id="updateItem")
async def update_item(
    item_id: uuid.UUID,
    data: ItemUpdate,
    current_user: CurrentUser,
    item_service: ItemServiceDep,
) -> ItemPublic:
    item = await item_service.get_or_404(item_id, current_user.id)
    updated = await item_service.update(item, data)
    return ItemPublic.model_validate(updated)


@router.delete("/{item_id}", response_model=Message, operation_id="deleteItem")
async def delete_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    item_service: ItemServiceDep,
) -> Message:
    item = await item_service.get_or_404(item_id, current_user.id)
    await item_service.delete(item)
    return Message(message="Item deleted")
