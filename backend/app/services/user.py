import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def create(self, data: UserCreate) -> User:
        if await self._repo.email_exists(data.email):
            raise ConflictError(f"Email {data.email!r} is already registered")
        return await self._repo.create(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_active=True,
            is_superuser=False,
        )

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.email and data.email != user.email:
            if await self._repo.email_exists(data.email):
                raise ConflictError(f"Email {data.email!r} is already taken")

        update_kwargs: dict[str, object] = data.model_dump(
            exclude_unset=True, exclude={"password"}
        )
        if data.password:
            update_kwargs["hashed_password"] = hash_password(data.password)

        return await self._repo.update(user, **update_kwargs)

    async def get_or_404(self, user_id: object) -> User:
        user = await self._repo.get_by_id(uuid.UUID(str(user_id)))
        if user is None:
            raise NotFoundError("User", user_id)
        return user
