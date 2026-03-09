"""
Test item endpoints.
Uses async pattern with pytest-asyncio.
"""

import uuid

import pytest

from app.core.config import settings
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.schemas.item import ItemCreate
from tests.utils.item import create_random_item
from tests.utils.utils import random_lower_string


@pytest.mark.asyncio
async def test_create_item(client, superuser_token_headers):
    """Test create item."""
    data = {"title": "Foo", "description": "Fighters"}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


@pytest.mark.asyncio
async def test_read_item(client, superuser_token_headers):
    """Test read item."""
    # Create item owned by superuser via API
    data = {"title": "Test Item", "description": "Test Description"}
    create_response = await client.post(
        f"{settings.API_V1_PREFIX}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    response = await client.get(
        f"{settings.API_V1_PREFIX}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == item_id


@pytest.mark.asyncio
async def test_read_item_not_found(client, superuser_token_headers):
    """Test read non-existing item returns 404."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_read_item_not_enough_permissions(
    client, normal_user_token_headers, session
):
    """Test read item without permission returns 403."""
    item = await create_random_item(session)

    response = await client.get(
        f"{settings.API_V1_PREFIX}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_items(client, superuser_token_headers, session):
    """Test read items list."""
    await create_random_item(session)
    await create_random_item(session)

    response = await client.get(
        f"{settings.API_V1_PREFIX}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


@pytest.mark.asyncio
async def test_read_items_as_normal_user_only_own_items(
    client, normal_user_token_headers, session
):
    """Non-superuser GET /items/ returns only their items."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(settings.FIRST_SUPERUSER)

    item_repo = ItemRepository(session)
    await item_repo.create(
        title=random_lower_string(),
        description=random_lower_string(),
        owner_id=user.id,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/items/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for item in content["data"]:
        assert item["owner_id"] != str(user.id)


@pytest.mark.asyncio
async def test_update_item(client, superuser_token_headers):
    """Test update item."""
    # Create item owned by superuser via API
    data = {"title": "Test Item", "description": "Test Description"}
    create_response = await client.post(
        f"{settings.API_V1_PREFIX}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    update_data = {"title": "Updated Title"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/items/{item_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_item_not_found(client, superuser_token_headers):
    """Test update non-existing item returns 404."""
    data = {"title": "Updated Title"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item_not_enough_permissions(
    client, normal_user_token_headers, session
):
    """Test update item without permission returns 403."""
    item = await create_random_item(session)

    data = {"title": "Updated Title"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_item(client, superuser_token_headers):
    """Test delete item."""
    # Create item owned by superuser via API
    data = {"title": "Test Item", "description": "Test Description"}
    create_response = await client.post(
        f"{settings.API_V1_PREFIX}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    response = await client.delete(
        f"{settings.API_V1_PREFIX}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted"

    # Verify item is deleted
    get_response = await client.get(
        f"{settings.API_V1_PREFIX}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_found(client, superuser_token_headers):
    """Test delete non-existing item returns 404."""
    response = await client.delete(
        f"{settings.API_V1_PREFIX}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_enough_permissions(
    client, normal_user_token_headers, session
):
    """Test delete item without permission returns 403."""
    item = await create_random_item(session)

    response = await client.delete(
        f"{settings.API_V1_PREFIX}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
