from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))
