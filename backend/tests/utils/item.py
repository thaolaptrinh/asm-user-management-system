"""
Test item utilities.
"""

from app.core.security import hash_password
from app.models.item import Item
from app.models.user import User
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.schemas.item import ItemCreate
from tests.utils.utils import random_lower_string


async def create_random_item(session, owner_id=None):
    """Create a random item for testing."""
    if owner_id is None:
        user_repo = UserRepository(session)
        user = await user_repo.create(
            email=f"{random_lower_string()}@example.com",
            hashed_password=hash_password(random_lower_string()),
            is_active=True,
            is_superuser=False,
        )
        owner_id = user.id

    item_repo = ItemRepository(session)
    item = await item_repo.create(
        title=random_lower_string(),
        description=random_lower_string(),
        owner_id=owner_id,
    )
    return item
