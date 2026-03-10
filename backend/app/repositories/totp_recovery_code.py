from datetime import UTC, datetime
from typing import List

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.totp_recovery_code import TotpRecoveryCode
from app.repositories.base import BaseRepository


class TotpRecoveryCodeRepository(BaseRepository[TotpRecoveryCode]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TotpRecoveryCode, session)

    async def get_by_user_id(self, user_id: str) -> List[TotpRecoveryCode]:
        result = await self.session.execute(
            select(TotpRecoveryCode)
            .where(TotpRecoveryCode.user_id == user_id)
            .order_by(TotpRecoveryCode.created_at)
        )
        return list(result.scalars().all())

    async def get_unused_by_user_id(self, user_id: str) -> List[TotpRecoveryCode]:
        result = await self.session.execute(
            select(TotpRecoveryCode)
            .where(
                and_(
                    TotpRecoveryCode.user_id == user_id,
                    TotpRecoveryCode.used_at.is_(None),
                )
            )
            .order_by(TotpRecoveryCode.created_at)
        )
        return list(result.scalars().all())

    async def create_batch(
        self, user_id: str, code_hashes: List[str]
    ) -> List[TotpRecoveryCode]:
        recovery_codes = [
            TotpRecoveryCode(
                user_id=user_id,
                code_hash=code_hash,
                used_at=None,
                created_at=datetime.now(UTC),
            )
            for code_hash in code_hashes
        ]
        self.session.add_all(recovery_codes)
        await self.session.flush()
        return recovery_codes

    async def verify_and_mark_used(self, user_id: str, code_hash: str) -> bool:
        result = await self.session.execute(
            select(TotpRecoveryCode).where(
                and_(
                    TotpRecoveryCode.user_id == user_id,
                    TotpRecoveryCode.code_hash == code_hash,
                    TotpRecoveryCode.used_at.is_(None),
                )
            )
        )
        code = result.scalar_one_or_none()

        if code is None:
            return False

        code.used_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def get_remaining_count(self, user_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(TotpRecoveryCode)
            .where(
                and_(
                    TotpRecoveryCode.user_id == user_id,
                    TotpRecoveryCode.used_at.is_(None),
                )
            )
        )
        return result.scalar_one() or 0

    async def delete_all(self, user_id: str) -> None:
        await self.session.execute(
            delete(TotpRecoveryCode).where(TotpRecoveryCode.user_id == user_id)
        )
        await self.session.flush()

    async def get_by_user_id_and_code_hash(
        self, user_id: str, code_hash: str
    ) -> TotpRecoveryCode | None:
        result = await self.session.execute(
            select(TotpRecoveryCode).where(
                and_(
                    TotpRecoveryCode.user_id == user_id,
                    TotpRecoveryCode.code_hash == code_hash,
                )
            )
        )
        return result.scalar_one_or_none()
