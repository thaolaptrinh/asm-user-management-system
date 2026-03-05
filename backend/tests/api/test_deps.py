"""Tests for app.api.deps (get_current_user, get_current_active_superuser)."""

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.security import create_access_token
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


def test_get_current_user_invalid_token_returns_403(client: TestClient) -> None:
    """Invalid or malformed token -> 403 Could not validate credentials."""
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_get_current_user_valid_token_user_not_found_returns_404(
    client: TestClient,
) -> None:
    """Valid JWT but user_id not in DB -> 404 User not found."""
    unknown_id = uuid.uuid4()
    token = create_access_token(
        subject=str(unknown_id), expires_delta=timedelta(minutes=15)
    )
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_get_current_user_inactive_returns_400(client: TestClient, db: Session) -> None:
    """Valid token but user is_active=False -> 400 Inactive user."""
    user_in = UserCreate(
        email=random_email(),
        password=random_lower_string(),
        is_active=False,
    )
    user = crud.create_user(session=db, user_create=user_in)
    token = create_access_token(
        subject=str(user.id), expires_delta=timedelta(minutes=15)
    )
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"
