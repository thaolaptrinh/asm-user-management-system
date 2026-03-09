import uuid

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID

    model_config = {"from_attributes": True}
