import uuid

from fastapi import APIRouter

from app.api.v1.deps import CurrentUser, SuperuserDep, UserRepoDep, UserServiceDep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.common import Message, PaginatedResponse
from app.schemas.user import UserCreate, UserPublic, UserUpdate, UserUpdateMe

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic, operation_id="getMe")
async def get_me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.patch("/me", response_model=UserPublic, operation_id="updateMe")
async def update_me(
    data: UserUpdateMe,
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> UserPublic:
    updated = await user_service.update(
        current_user, UserUpdate(**data.model_dump(exclude_unset=True))
    )
    return UserPublic.model_validate(updated)


@router.get("/", response_model=PaginatedResponse[UserPublic], operation_id="listUsers")
async def list_users(
    _: SuperuserDep,
    user_repo: UserRepoDep,
    skip: int = 0,
    limit: int = 100,
) -> PaginatedResponse[UserPublic]:
    users = await user_repo.get_all(skip=skip, limit=limit)
    count = await user_repo.count()
    return PaginatedResponse(
        data=[UserPublic.model_validate(u) for u in users],
        count=count,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=UserPublic, status_code=201, operation_id="createUser")
async def create_user(
    data: UserCreate,
    _: SuperuserDep,
    user_service: UserServiceDep,
) -> UserPublic:
    user = await user_service.create(data)
    return UserPublic.model_validate(user)


@router.get("/{user_id}", response_model=UserPublic, operation_id="getUser")
async def get_user(
    user_id: uuid.UUID,
    _: SuperuserDep,
    user_service: UserServiceDep,
) -> UserPublic:
    user = await user_service.get_or_404(user_id)
    return UserPublic.model_validate(user)


@router.patch("/{user_id}", response_model=UserPublic, operation_id="updateUser")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    _: SuperuserDep,
    user_service: UserServiceDep,
) -> UserPublic:
    user = await user_service.get_or_404(user_id)
    updated = await user_service.update(user, data)
    return UserPublic.model_validate(updated)


@router.delete("/{user_id}", response_model=Message, operation_id="deleteUser")
async def delete_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    _: SuperuserDep,
    user_repo: UserRepoDep,
) -> Message:
    if str(user_id) == str(current_user.id):
        raise ForbiddenError("Cannot delete your own account")
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    await user_repo.delete(user)
    return Message(message="User deleted")
