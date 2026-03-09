"""Seed script for initial data."""

import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.item import Item
from app.models.user import User


async def seed() -> None:
    """Seed database with initial data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("Seeding database...")

        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        )
        existing_superuser = result.scalar_one_or_none()

        if existing_superuser:
            print(f"Superuser {settings.FIRST_SUPERUSER} already exists, skipping seed")
            return

        superuser = User(
            email=settings.FIRST_SUPERUSER,
            full_name="Admin User",
            hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            is_superuser=True,
        )

        session.add(superuser)
        await session.commit()
        await session.refresh(superuser)
        print(f"Created superuser: {superuser.email}")

        seed_items = [
            Item(
                title=f"Sample Item {i}",
                description="This is a sample item created during seeding.",
                owner_id=superuser.id,
            )
            for i in range(1, 6)
        ]

        session.add_all(seed_items)
        await session.commit()
        for item in seed_items:
            await session.refresh(item)
        print(f"Created {len(seed_items)} sample items")

        print("Database seeded successfully!")


async def main() -> None:
    """Main entry point."""
    try:
        await seed()
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
