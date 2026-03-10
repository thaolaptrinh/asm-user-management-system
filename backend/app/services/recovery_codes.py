import secrets
import string
from typing import List

import bcrypt

from app.repositories.totp_recovery_code import TotpRecoveryCodeRepository


class RecoveryCodesService:
    CODE_COUNT = 10
    CODE_LENGTH = 8
    CODE_FORMAT = "XXXX-XXXX"
    BCRYPT_ROUNDS = 12

    def __init__(self, repo: TotpRecoveryCodeRepository) -> None:
        self._repo = repo

    def generate_codes(self) -> List[str]:
        codes = []
        for _ in range(self.CODE_COUNT):
            code = self._generate_single_code()
            codes.append(code)
        return codes

    def _generate_single_code(self) -> str:
        chars = string.ascii_uppercase.replace("O", "").replace("I", "")
        code = "".join(secrets.choice(chars) for _ in range(self.CODE_LENGTH))
        return self._format_code(code)

    def _format_code(self, code: str) -> str:
        return f"{code[:4]}-{code[4:]}"

    def hash_code(self, code: str) -> str:
        normalized = self.normalize_code(code)
        return bcrypt.hashpw(
            normalized.encode("utf-8"), bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        ).decode("utf-8")

    def verify_code_hash(self, code: str, code_hash: str) -> bool:
        normalized = self.normalize_code(code)
        return bcrypt.checkpw(normalized.encode("utf-8"), code_hash.encode("utf-8"))

    def normalize_code(self, code: str) -> str:
        return code.upper().replace("-", "").replace(" ", "")

    async def generate_for_user(self, user_id: str) -> List[str]:
        await self._repo.delete_all(user_id)

        plaintext_codes = self.generate_codes()
        code_hashes = [self.hash_code(code) for code in plaintext_codes]

        await self._repo.create_batch(user_id, code_hashes)

        return plaintext_codes

    async def verify(self, user_id: str, code: str) -> bool:
        normalized = self.normalize_code(code)
        if len(normalized) != self.CODE_LENGTH:
            return False

        # Load all unused hashes and check each with bcrypt — bcrypt is non-deterministic
        # (new salt per hash_code() call), so we cannot hash the input and match directly.
        unused_codes = await self._repo.get_unused_by_user_id(user_id)
        for recovery_code in unused_codes:
            if self.verify_code_hash(normalized, recovery_code.code_hash):
                return await self._repo.verify_and_mark_used(
                    user_id, recovery_code.code_hash
                )
        return False

    async def get_remaining_count(self, user_id: str) -> int:
        return await self._repo.get_remaining_count(user_id)

    async def regenerate(self, user_id: str) -> List[str]:
        return await self.generate_for_user(user_id)
