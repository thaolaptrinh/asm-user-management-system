"""
Test utility endpoints.
Uses async pattern with pytest-asyncio.

Note: /utils/health-check/ and /utils/test-email/ endpoints are not implemented in current version.
"""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check(client):
    """GET /health returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
