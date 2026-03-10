"""Drop and recreate database - for testing only."""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def drop_database() -> None:
    """Drop and recreate database from settings."""
    # Connect to MySQL server without database
    db_url = str(settings.DATABASE_URL).rsplit("/", 1)[0]
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {settings.DB_DATABASE}"))
        await conn.execute(
            text(
                f"CREATE DATABASE {settings.DB_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(drop_database())
