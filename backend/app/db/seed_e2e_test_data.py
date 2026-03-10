"""Seed E2E test data with deterministic users and credentials.

This script creates test users with known credentials for E2E testing.
All credentials are fixed to ensure tests are deterministic and reproducible.

Test Users Created:
- test-user@example.com / TestPassword123! (with TOTP, recovery code: ABCD-1234)
- admin@example.com / TestPassword123! (superuser, with TOTP, recovery code: ADMN-1111)
- test-user-no-totp@example.com / TestPassword123! (no TOTP, for signup tests)
"""

import asyncio
import secrets
import string

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.totp_recovery_code import TotpRecoveryCode
from app.models.totp_secret import TotpSecret
from app.models.user import User
from app.services.recovery_codes import RecoveryCodesService

_recovery_codes_service = RecoveryCodesService(repo=None)  # type: ignore[arg-type]


def generate_recovery_code() -> str:
    """Generate a recovery code in format XXXX-XXXX."""
    part1 = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    part2 = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"{part1}-{part2}"


async def create_user_with_totp(
    session,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool = False,
    totp_secret: str = "JBSWY3DPEHPK3PXP",
    recovery_codes: list | None = None,
) -> User:
    """Create a user with TOTP enabled and recovery codes."""
    from sqlalchemy import delete

    # Delete existing user if present
    await session.execute(delete(User).where(User.email == email))

    # Create user
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create TOTP secret (pre-verified)
    secret = TotpSecret(
        user_id=user.id,
        secret=totp_secret,
        is_verified=True,
    )
    session.add(secret)

    # Generate or use provided recovery codes
    if recovery_codes is None:
        recovery_codes = [generate_recovery_code() for _ in range(10)]

    for code in recovery_codes:
        recovery_code = TotpRecoveryCode(
            user_id=user.id,
            code_hash=_recovery_codes_service.hash_code(code),
        )
        session.add(recovery_code)

    await session.commit()
    return user


async def create_user_without_totp(
    session,
    email: str,
    password: str,
    full_name: str,
) -> User:
    """Create a user without TOTP (for signup/enrollment tests)."""
    from sqlalchemy import delete

    # Delete existing user if present
    await session.execute(delete(User).where(User.email == email))

    # Create user
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def seed_e2e_test_data() -> None:
    """Seed all E2E test data."""
    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("🌱 Seeding E2E test data...")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        # User 1: Standard user with TOTP
        print("Creating standard user with TOTP...")
        user1 = await create_user_with_totp(
            session,
            email="test-user@example.com",
            password="TestPassword123!",
            full_name="E2E Test User",
            is_superuser=False,
            totp_secret="JBSWY3DPEHPK3PXP",
            recovery_codes=[
                "ABCD-1234", "EFGH-5678", "IJKL-9012", "MNOP-3456", "QRST-7890",
                "UVWX-2345", "YZAB-6789", "CDEF-0123", "GHIJ-4567", "KLMN-8901"
            ],
        )
        print(f"  ✅ {user1.email}")
        print(f"     Password: TestPassword123!")
        print(f"     TOTP: Enabled (secret: JBSWY3DPEHPK3PXP)")
        print(f"     Recovery codes: 10 generated")
        print(f"     First code: ABCD-1234")

        # User 2: Admin user with TOTP
        print("\nCreating admin user with TOTP...")
        user2 = await create_user_with_totp(
            session,
            email="admin@example.com",
            password="TestPassword123!",
            full_name="E2E Admin User",
            is_superuser=True,
            totp_secret="JBSWY3DPEHPK3PXP",
            recovery_codes=[
                "ADMN-1111", "ADMN-2222", "ADMN-3333", "ADMN-4444", "ADMN-5555",
                "ADMN-6666", "ADMN-7777", "ADMN-8888", "ADMN-9999", "ADMN-0000"
            ],
        )
        print(f"  ✅ {user2.email}")
        print(f"     Password: TestPassword123!")
        print(f"     TOTP: Enabled (secret: JBSWY3DPEHPK3PXP)")
        print(f"     Recovery codes: 10 generated")
        print(f"     First code: ADMN-1111")

        # User 3: User without TOTP (for signup/enrollment tests)
        print("\nCreating user without TOTP...")
        user3 = await create_user_without_totp(
            session,
            email="test-user-no-totp@example.com",
            password="TestPassword123!",
            full_name="E2E Test User (No TOTP)",
        )
        print(f"  ✅ {user3.email}")
        print(f"     Password: TestPassword123!")
        print(f"     TOTP: Not enabled (for enrollment tests)")

        print("\n" + "=" * 70)
        print("✅ E2E test data seeded successfully!")
        print("\n📋 Test User Credentials:")
        print("   Standard User: test-user@example.com / TestPassword123!")
        print("   Admin User: admin@example.com / TestPassword123!")
        print("   No TOTP User: test-user-no-totp@example.com / TestPassword123!")
        print("\n🔑 Recovery Codes (first code):")
        print("   Standard: ABCD-1234")
        print("   Admin: ADMN-1111")
        print("=" * 70)


async def main() -> None:
    """Main entry point."""
    try:
        await seed_e2e_test_data()
    except Exception as e:
        print(f"❌ Error seeding test data: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
