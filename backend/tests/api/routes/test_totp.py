"""
API-level tests for TOTP endpoints.

All TOTP verification logic is mocked at the service layer —
these tests focus on routing, request/response contracts, auth enforcement,
and HTTP status codes.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, create_temp_token, hash_password
from app.schemas.totp import (
    TotpChallengeResponse,
    TotpEnrollResponse,
    TotpStatusResponse,
    TotpVerifyFlowAResponse,
    TotpVerifyFlowBResponse,
)

BASE = f"{settings.API_V1_PREFIX}/auth/totp"


# ── GET /auth/totp/status ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_status_with_access_token(
    client, totp_user_access_headers, sample_user_with_totp
):
    """GET /auth/totp/status returns is_enabled=True for a user with verified TOTP."""
    response = await client.get(f"{BASE}/status", headers=totp_user_access_headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_totp_status_with_temp_token(client, totp_user_temp_headers):
    """GET /auth/totp/status accepts temp_token."""
    response = await client.get(f"{BASE}/status", headers=totp_user_temp_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_totp_status_no_token(client):
    """GET /auth/totp/status returns 401 without token."""
    response = await client.get(f"{BASE}/status")
    assert response.status_code == 401


# ── POST /auth/totp/enroll ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_enroll_success(client, totp_user_temp_headers):
    """POST /auth/totp/enroll returns secret + qr_code + otpauth_url."""
    mock_response = TotpEnrollResponse(
        secret="JBSWY3DPEHPK3PXP",
        qr_code="data:image/png;base64,abc123",
        otpauth_url="otpauth://totp/App:test@example.com?secret=JBSWY3DPEHPK3PXP",
    )
    with patch(
        "app.services.totp.TotpService.create_totp_for_user",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(f"{BASE}/enroll", headers=totp_user_temp_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["secret"] == "JBSWY3DPEHPK3PXP"
    assert data["qr_code"].startswith("data:image/png;base64,")
    assert data["otpauth_url"].startswith("otpauth://totp/")


@pytest.mark.asyncio
async def test_totp_enroll_invalid_token(client):
    """POST /auth/totp/enroll returns 401 with invalid token."""
    response = await client.post(
        f"{BASE}/enroll", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_enroll_stores_secret_with_is_verified_false(client, session):
    """Verify TOTP secret is stored in database with is_verified=False."""
    from app.models.user import User
    from app.repositories.totp_secret import TotpSecretRepository

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"enroll_test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    temp_token = create_temp_token(str(user.id))
    headers = {"Authorization": f"Bearer {temp_token}"}

    response = await client.post(f"{BASE}/enroll", headers=headers)
    assert response.status_code == 200

    repo = TotpSecretRepository(session)
    totp = await repo.get_by_user_id(str(user_id))
    assert totp is not None
    assert totp.is_verified is False


@pytest.mark.asyncio
async def test_totp_enroll_already_active_returns_409(client, totp_user_access_headers):
    """POST /auth/totp/enroll returns 409 when TOTP is already active."""
    with patch(
        "app.services.totp.TotpService.create_totp_for_user",
        new_callable=AsyncMock,
        side_effect=ConflictError("TOTP is already enabled"),
    ):
        response = await client.post(f"{BASE}/enroll", headers=totp_user_access_headers)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_totp_enroll_no_token(client):
    """POST /auth/totp/enroll returns 401 without token."""
    response = await client.post(f"{BASE}/enroll")
    assert response.status_code == 401


# ── POST /auth/totp/challenge ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_challenge_success(client, totp_user_temp_headers):
    """POST /auth/totp/challenge returns challenge_id and expires_in."""
    challenge_id = uuid.uuid4()
    mock_response = TotpChallengeResponse(challenge_id=challenge_id, expires_in=60)

    with patch(
        "app.services.totp.TotpService.create_challenge",
        return_value=mock_response,
    ):
        response = await client.post(
            f"{BASE}/challenge", headers=totp_user_temp_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["challenge_id"] == str(challenge_id)
    assert data["expires_in"] == 60


@pytest.mark.asyncio
async def test_totp_challenge_no_token(client):
    """POST /auth/totp/challenge returns 401 without token."""
    response = await client.post(f"{BASE}/challenge")
    assert response.status_code == 401


# ── POST /auth/totp/verify — Flow A ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_verify_flow_a_success(client, session):
    """Flow A: valid temp_token + valid totp_code returns access_token."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "123456"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data
    assert data["user"]["email"] == user.email
    # Backend must set the HttpOnly access_token cookie so the browser can use it
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_totp_verify_flow_a_invalid_temp_token(client):
    """Flow A: invalid temp_token returns 401."""
    response = await client.post(
        f"{BASE}/verify",
        json={"temp_token": "not.a.valid.jwt", "totp_code": "123456"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_flow_a_access_token_rejected(client, session):
    """Flow A: using access_token as temp_token must be rejected."""
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_access_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
        password_version=1,
    )
    session.add(user)
    await session.flush()

    # Access token (type="access") must not work as temp_token
    access_token = create_access_token(str(user.id), user.password_version)
    response = await client.post(
        f"{BASE}/verify",
        json={"temp_token": access_token, "totp_code": "123456"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_flow_a_wrong_code(client, session):
    """Flow A: valid temp_token but wrong TOTP code returns 401 with exact message."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_wrong_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("Invalid TOTP code"),
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "000000"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid TOTP code"


# ── POST /auth/totp/verify — Flow B ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_verify_flow_b_success(client, totp_service, sample_user_with_totp):
    """Flow B: valid challenge_id + totp_code returns is_enabled=True."""
    # Make TOTP unverified so enrollment verify works
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        await totp_service._repo.session.flush()

    challenge_resp = totp_service.create_challenge(str(sample_user_with_totp.id))

    with patch(
        "app.services.totp.TotpService.verify_totp_for_enrollment",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={
                "challenge_id": str(challenge_resp.challenge_id),
                "totp_code": "123456",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is True
    assert "message" in data
    assert "recovery_codes" in data
    assert isinstance(data["recovery_codes"], list)
    assert len(data["recovery_codes"]) == 10  # RecoveryCodesService.CODE_COUNT


@pytest.mark.asyncio
async def test_totp_verify_flow_b_expired_challenge(client):
    """Flow B: expired/unknown challenge_id returns 401."""
    response = await client.post(
        f"{BASE}/verify",
        json={"challenge_id": str(uuid.uuid4()), "totp_code": "123456"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_flow_b_wrong_code(
    client, totp_service, sample_user_with_totp
):
    """Flow B: valid challenge_id but wrong code returns 401."""
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        await totp_service._repo.session.flush()

    challenge_resp = totp_service.create_challenge(str(sample_user_with_totp.id))

    with patch(
        "app.services.totp.TotpService.verify_totp_for_enrollment",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("Invalid TOTP code"),
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={
                "challenge_id": str(challenge_resp.challenge_id),
                "totp_code": "000000",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_flow_a_expired_otp(client, session):
    """Flow A: OTP code outside valid time window returns 401."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_expired_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    # Use OTP code that is far outside the valid time window
    # This will cause _find_accepted_counter to return None
    with patch(
        "app.services.totp.TotpService._find_accepted_counter",
        return_value=None,
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "999999"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid TOTP code"


@pytest.mark.asyncio
async def test_totp_verify_flow_a_replay_attack_api_level(client, session):
    """Flow A: Using same OTP code twice returns 401 on second request (API level)."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret
    from unittest.mock import AsyncMock, patch

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_replay_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
        last_used_counter=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    # Mock first request to succeed
    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response1 = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "123456"},
        )
        assert response1.status_code == 200

    # Mock second request to fail with replay attack error
    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("TOTP code already used in current window"),
    ):
        response2 = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "123456"},
        )
        assert response2.status_code == 401
        assert response2.json()["detail"] == "TOTP code already used in current window"


@pytest.mark.asyncio
async def test_totp_verify_flow_a_missing_temp_token(client, session):
    """Flow A: Request without temp_token (only totp_code) returns 422."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_no_temp_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    # Request without temp_token (only totp_code and challenge_id)
    response = await client.post(
        f"{BASE}/verify",
        json={"totp_code": "123456"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_totp_verify_totp_code_7_digits(client):
    """POST /auth/totp/verify with 7-digit totp_code should be rejected (schema allows 6-8 but service uses 6)."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_7digit_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    # 7-digit code passes schema validation but service should reject
    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("Invalid TOTP code"),
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "1234567"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_totp_code_8_digits(client):
    """POST /auth/totp/verify with 8-digit totp_code should be rejected (schema allows 6-8 but service uses 6)."""
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"flow_a_8digit_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    # 8-digit code passes schema validation but service should reject
    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("Invalid TOTP code"),
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "12345678"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_flow_b_replay_attack(
    client, totp_service, sample_user_with_totp
):
    """Flow B: Using same OTP code twice returns 401 on second request."""
    # Make TOTP unverified so enrollment verify works
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        await totp_service._repo.session.flush()

    challenge_resp = totp_service.create_challenge(str(sample_user_with_totp.id))

    # Mock first request to succeed
    with patch(
        "app.services.totp.TotpService.verify_totp_for_enrollment",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response1 = await client.post(
            f"{BASE}/verify",
            json={
                "challenge_id": str(challenge_resp.challenge_id),
                "totp_code": "123456",
            },
        )
        assert response1.status_code == 200

    # Mock second request to fail with replay attack error
    with patch(
        "app.services.totp.TotpService.verify_totp_for_enrollment",
        new_callable=AsyncMock,
        side_effect=UnauthorizedError("TOTP code already used in current window"),
    ):
        response2 = await client.post(
            f"{BASE}/verify",
            json={
                "challenge_id": str(challenge_resp.challenge_id),
                "totp_code": "123456",
            },
        )
        assert response2.status_code == 401
        assert response2.json()["detail"] == "TOTP code already used in current window"


# ── Request validation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_totp_verify_missing_both_fields(client):
    """POST /auth/totp/verify with neither temp_token nor challenge_id returns 422."""
    response = await client.post(
        f"{BASE}/verify",
        json={"totp_code": "123456"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_totp_verify_both_fields_provided(client):
    """POST /auth/totp/verify with both temp_token and challenge_id is valid (Flow B with binding).
    The request passes validation — the server will reject it at the logic level (invalid tokens),
    not at the schema level.
    """
    response = await client.post(
        f"{BASE}/verify",
        json={
            "temp_token": "some.token",
            "challenge_id": str(uuid.uuid4()),
            "totp_code": "123456",
        },
    )
    # Schema is valid; should fail at the auth/logic level (401), not validation (422)
    assert response.status_code != 422


@pytest.mark.asyncio
async def test_totp_verify_totp_code_too_short(client):
    """POST /auth/totp/verify with totp_code < 6 chars returns 422."""
    response = await client.post(
        f"{BASE}/verify",
        json={"temp_token": "some.token", "totp_code": "123"},
    )
    assert response.status_code == 422


# ── POST /auth/totp/recovery/verify ─────────────────────────────────────────

RECOVERY_BASE = f"{settings.API_V1_PREFIX}/auth/totp/recovery"


@pytest.mark.asyncio
async def test_recovery_verify_success_sets_cookie(client, session):
    """Recovery code verify: valid code sets access_token cookie and returns access_token."""
    from unittest.mock import AsyncMock, patch
    from app.core.security import hash_password, create_temp_token
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"recovery_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with (
        patch(
            "app.services.recovery_codes.RecoveryCodesService.verify",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.recovery_codes.RecoveryCodesService.get_remaining_count",
            new_callable=AsyncMock,
            return_value=9,
        ),
    ):
        response = await client.post(
            f"{RECOVERY_BASE}/verify",
            json={"temp_token": temp_token, "code": "ABCD-1234"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "success" not in data
    assert data["remaining_count"] == 9
    assert data["access_token"] is not None
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_recovery_verify_invalid_code_returns_401(client, session):
    """Recovery code verify: invalid code returns 401, no cookie."""
    from unittest.mock import AsyncMock, patch
    from app.core.security import hash_password, create_temp_token
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"recovery_bad_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with patch(
        "app.services.recovery_codes.RecoveryCodesService.verify",
        new_callable=AsyncMock,
        return_value=False,
    ):
        response = await client.post(
            f"{RECOVERY_BASE}/verify",
            json={"temp_token": temp_token, "code": "XXXX-0000"},
        )

    assert response.status_code == 401
    assert "access_token" not in response.cookies


@pytest.mark.asyncio
async def test_recovery_verify_invalid_temp_token_returns_401(client):
    """Recovery code verify: invalid temp_token returns 401."""
    response = await client.post(
        f"{RECOVERY_BASE}/verify",
        json={"temp_token": "not.a.valid.jwt", "code": "ABCD-1234"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_recovery_status_requires_auth(client):
    """GET /auth/totp/recovery returns 401 without token."""
    response = await client.get(RECOVERY_BASE)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify_includes_password_version(client, session):
    """TOTP verify endpoint returns access_token with password_version in payload."""
    from app.core.security import hash_password, decode_access_token
    from app.models.user import User
    from app.models.totp_secret import TotpSecret

    user = User(
        id=uuid.uuid4(),
        email=f"pwd_ver_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
        password_version=3,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with patch(
        "app.services.totp.TotpService.verify_totp_for_login",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await client.post(
            f"{BASE}/verify",
            json={"temp_token": temp_token, "totp_code": "123456"},
        )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["password_version"] == 3
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_recovery_verify_includes_password_version(client, session):
    """Recovery code verify endpoint returns access_token with password_version in payload."""
    from app.core.security import hash_password, decode_access_token
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"rec_pwd_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
        password_version=7,
    )
    session.add(user)
    await session.flush()

    temp_token = create_temp_token(str(user.id))

    with (
        patch(
            "app.services.recovery_codes.RecoveryCodesService.verify",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.recovery_codes.RecoveryCodesService.get_remaining_count",
            new_callable=AsyncMock,
            return_value=9,
        ),
    ):
        response = await client.post(
            f"{RECOVERY_BASE}/verify",
            json={"temp_token": temp_token, "code": "ABCD-1234"},
        )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["password_version"] == 7
    assert payload["type"] == "access"
