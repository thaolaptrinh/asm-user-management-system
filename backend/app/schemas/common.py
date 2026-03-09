from pydantic import BaseModel


class Message(BaseModel):
    message: str


class PaginatedResponse[T](BaseModel):
    data: list[T]
    count: int
    skip: int
    limit: int
