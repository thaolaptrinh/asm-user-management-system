from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.totp_secret import TotpSecret
from app.repositories.base import BaseRepository


class TotpSecretRepository(BaseRepository[TotpSecret]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TotpSecret, session)

    async def get_by_user_id(self, user_id: str) -> TotpSecret | None:
        result = await self.session.execute(
            select(TotpSecret).where(TotpSecret.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: str,
        secret: str,
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
    ) -> TotpSecret:
        existing = await self.get_by_user_id(user_id)

        if existing:
            existing.secret = secret
            existing.algorithm = algorithm
            existing.digits = digits
            existing.period = period
            existing.is_verified = False
            existing.last_used_at = None
            existing.last_used_counter = None
            self.session.add(existing)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        return await self.create(
            user_id=user_id,
            secret=secret,
            algorithm=algorithm,
            digits=digits,
            period=period,
            is_verified=False,
            last_used_at=None,
            last_used_counter=None,
        )

    async def mark_verified(self, user_id: str) -> None:
        await self.session.execute(
            update(TotpSecret)
            .where(TotpSecret.user_id == user_id)
            .values(is_verified=True)
        )
        await self.session.flush()

    async def update_last_used(self, user_id: str, counter: int) -> None:
        await self.session.execute(
            update(TotpSecret)
            .where(TotpSecret.user_id == user_id)
            .values(
                last_used_at=datetime.now(timezone.utc),
                last_used_counter=counter,
            )
        )
        await self.session.flush()

    async def check_last_used_counter(
        self, user_id: str, accepted_counter: int
    ) -> bool:
        """
        Return True if `accepted_counter` has already been used (replay attack).
        A counter value is considered replayed when last_used_counter >= accepted_counter.
        """
        totp_secret = await self.get_by_user_id(user_id)
        if not totp_secret or totp_secret.last_used_counter is None:
            return False
        return totp_secret.last_used_counter >= accepted_counter
