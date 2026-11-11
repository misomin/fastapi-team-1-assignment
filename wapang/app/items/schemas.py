from pydantic import BaseModel, ConfigDict, Field, field_validator
from wapang.common.exceptions import InvalidFormatException

class ItemCreateRequest(BaseModel):
    item_name: str
    price: int = Field(strict=True, ge=0)
    stock: int = Field(strict=True, ge=0)

    @field_validator("item_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not 2 <= len(value) <= 50:
            raise InvalidFormatException()
        return value

class ItemUpdateRequest(BaseModel):
    item_name: str | None = None
    price: int | None = None
    stock: int | None = None

    @field_validator("item_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        if value is None or not 2 <= len(value) <= 50:
            raise InvalidFormatException()
        return value

    @field_validator("price", "stock", mode="before")
    @classmethod
    def validate_nonnegative(cls, value: int | None) -> int:
        if value is None or type(value) is not int or value < 0:
            raise InvalidFormatException()
        return value

class ItemResponse(BaseModel):
    id: str
    item_name: str = Field(validation_alias="name")
    price: int
    stock: int

    model_config = ConfigDict(from_attributes=True)

class ItemListResponse(BaseModel):
    id: str
    item_name: str
    price: int
    stock: int
    store_id: str
    store_name: str