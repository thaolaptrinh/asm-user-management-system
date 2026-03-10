import base64
import hashlib
import io
import uuid
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
import asyncio

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.repositories.totp_secret import TotpSecretRepository
from app.schemas.totp import (
    TotpChallengeResponse,
    TotpEnrollResponse,
    TotpStatusResponse,
)

CHALLENGE_TTL_SECONDS = 60

# In-memory challenge store: challenge_id -> {user_id, expires_at}
# Phase 1: single-server only. Migrate to Redis for multi-server.
_challenges: dict[str, dict] = {}


class TotpService:
    def __init__(self, totp_repo: TotpSecretRepository) -> None:
        self._repo = totp_repo

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    async def generate_qr_code(self, secret: str, email: str) -> str:
        """
        Generate QR code for TOTP secret.
        Offloads CPU-intensive QR generation to thread pool to avoid blocking event loop.
        """
        otpauth_url = self._get_otpauth_url(secret, email)

        def _blocking_qr_generation() -> str:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(otpauth_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        return await asyncio.to_thread(_blocking_qr_generation)

    def _get_otpauth_url(self, secret: str, email: str) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=settings.APP_NAME,
        )

    def _find_accepted_counter(
        self, secret: str, totp_code: str, algorithm: str, digits: int, period: int
    ) -> int | None:
        """
        Determine which TOTP counter value (unix_time // period) the code matches.
        Checks current window and ±1 adjacent windows (same as valid_window=1).
        Returns the accepted counter, or None if the code is invalid.
        """
        digest_map = {
            "SHA1": hashlib.sha1,
            "SHA256": hashlib.sha256,
            "SHA512": hashlib.sha512,
        }
        digest = digest_map.get(algorithm, hashlib.sha1)
        totp = pyotp.TOTP(secret, digits=digits, digest=digest)
        current_counter = int(datetime.now(timezone.utc).timestamp() // period)
        for offset in (-1, 0, 1):
            counter = current_counter + offset
            if totp.at(counter * period) == totp_code:
                return counter
        return None

    async def is_totp_enabled(self, user_id: str) -> bool:
        totp_secret = await self._repo.get_by_user_id(user_id)
        return totp_secret is not None and totp_secret.is_verified

    async def get_totp_status(self, user_id: str) -> TotpStatusResponse:
        is_enabled = await self.is_totp_enabled(user_id)
        message = "TOTP đã được kích hoạt" if is_enabled else "TOTP chưa được kích hoạt"
        return TotpStatusResponse(is_enabled=is_enabled, message=message)

    async def create_totp_for_user(
        self, user_id: str, email: str
    ) -> TotpEnrollResponse:
        existing = await self._repo.get_by_user_id(user_id)

        if existing and existing.is_verified:
            raise ConflictError("TOTP đã được kích hoạt")

        secret = self.generate_secret()
        qr_code = await self.generate_qr_code(secret, email)
        otpauth_url = self._get_otpauth_url(secret, email)

        await self._repo.create_or_update(
            user_id=user_id,
            secret=secret,
            algorithm="SHA1",
            digits=6,
            period=30,
        )

        return TotpEnrollResponse(
            secret=secret,
            qr_code=qr_code,
            otpauth_url=otpauth_url,
        )

    async def _verify_totp_with_replay_check(
        self,
        user_id: str,
        totp_code: str,
        check_verified: bool = True,
        mark_as_verified: bool = False,
    ) -> bool:
        """
        Common verification logic with replay attack prevention.

        Determines the exact counter value accepted by the code, then rejects the
        code if that counter has already been used (prevents reuse of a code across
        the current window and the adjacent ±1 windows).

        Args:
            user_id: User ID to verify
            totp_code: TOTP code from authenticator
            check_verified: Whether to check if TOTP is already verified (for login)
            mark_as_verified: Whether to mark TOTP as verified (for enrollment)

        Returns:
            True if verification successful

        Raises:
            UnauthorizedError: If TOTP not enabled, code invalid, or replay detected
            ConflictError: If TOTP already verified (during enrollment)
        """
        totp_secret = await self._repo.get_by_user_id(user_id)

        if not totp_secret:
            raise UnauthorizedError("TOTP secret không tồn tại")

        if check_verified and not totp_secret.is_verified:
            raise UnauthorizedError("TOTP chưa được kích hoạt")

        if mark_as_verified and totp_secret.is_verified:
            raise ConflictError("TOTP đã được kích hoạt")

        accepted_counter = self._find_accepted_counter(
            totp_secret.secret,
            totp_code,
            totp_secret.algorithm,
            totp_secret.digits,
            totp_secret.period,
        )

        if accepted_counter is None:
            raise UnauthorizedError("Mã TOTP không hợp lệ")

        if await self._repo.check_last_used_counter(user_id, accepted_counter):
            raise UnauthorizedError("Mã TOTP đã được sử dụng trong window hiện tại")

        if mark_as_verified:
            await self._repo.mark_verified(user_id)

        await self._repo.update_last_used(user_id, accepted_counter)
        return True

    async def verify_totp_for_login(self, user_id: str, totp_code: str) -> bool:
        return await self._verify_totp_with_replay_check(
            user_id=user_id,
            totp_code=totp_code,
            check_verified=True,
            mark_as_verified=False,
        )

    async def verify_totp_for_enrollment(self, user_id: str, totp_code: str) -> bool:
        return await self._verify_totp_with_replay_check(
            user_id=user_id,
            totp_code=totp_code,
            check_verified=False,
            mark_as_verified=True,
        )

    def create_challenge(self, user_id: str) -> TotpChallengeResponse:
        """Create in-memory challenge for TOTP enrollment (Step 2)."""
        self._purge_expired_challenges()

        challenge_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=CHALLENGE_TTL_SECONDS)
        _challenges[str(challenge_id)] = {
            "user_id": user_id,
            "expires_at": expires_at,
        }

        return TotpChallengeResponse(
            challenge_id=challenge_id,
            expires_in=CHALLENGE_TTL_SECONDS,
        )

    def resolve_challenge(self, challenge_id: str) -> str:
        """
        Resolve challenge_id to user_id.
        Raises UnauthorizedError if not found or expired.
        Consumes the challenge (single-use).
        """
        self._purge_expired_challenges()

        entry = _challenges.pop(str(challenge_id), None)
        if entry is None:
            raise UnauthorizedError("Challenge không hợp lệ hoặc đã hết hạn")

        if datetime.now(timezone.utc) > entry["expires_at"]:
            raise UnauthorizedError("Challenge không hợp lệ hoặc đã hết hạn")

        return entry["user_id"]

    def _purge_expired_challenges(self) -> None:
        """Remove expired challenges to prevent memory leak."""
        now = datetime.now(timezone.utc)
        expired = [cid for cid, v in _challenges.items() if now > v["expires_at"]]
        for cid in expired:
            _challenges.pop(cid, None)
