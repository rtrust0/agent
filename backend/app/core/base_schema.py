from typing import Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel

T = TypeVar("T")


class ResponseSchema(PydanticBaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None


class PageResult(PydanticBaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
