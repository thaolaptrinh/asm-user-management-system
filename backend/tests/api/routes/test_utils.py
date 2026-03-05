"""Tests for app.api.routes.utils (test-email, health-check)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_check(client: TestClient) -> None:
    """GET /utils/health-check/ returns True."""
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_test_email_superuser_success(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Superuser POST /utils/test-email/ sends test email and returns 201."""
    with (
        patch("app.utils.send_email", return_value=None),
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            headers=superuser_token_headers,
            params={"email_to": "test@example.com"},
        )
    assert r.status_code == 201
    assert r.json()["message"] == "Test email sent"


def test_test_email_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Non-superuser cannot call test-email -> 403."""
    r = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        headers=normal_user_token_headers,
        params={"email_to": "test@example.com"},
    )
    assert r.status_code == 403
