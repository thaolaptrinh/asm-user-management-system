from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)
    
    async def create(
        self,
        user_id: str | None,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "SUCCESS",
        meta: dict | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        import json
        return await super().create(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            meta=json.dumps(meta) if meta else None,
        )
