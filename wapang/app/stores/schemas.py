import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


PHONE_PATTERN = re.compile(r"010-[0-9]{4}-[0-9]{4}")


class StoreCreateRequest(BaseModel):
    store_name: str = Field(min_length=3, max_length=20)
    address: str = Field(max_length=100)
    email: EmailStr
    phone_number: str
    delivery_fee: int = Field(strict=True, ge=0)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if PHONE_PATTERN.fullmatch(value) is None:
            raise ValueError("Invalid phone number")
        return value


class StoreUpdateRequest(BaseModel):
    store_name: str | None = None
    address: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    delivery_fee: int | None = None

    @field_validator("store_name")
    @classmethod
    def validate_store_name(cls, value: str | None) -> str:
        if value is None or not 3 <= len(value) <= 20:
            raise ValueError("Invalid store name")
        return value

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str | None) -> str:
        if value is None or len(value) > 100:
            raise ValueError("Invalid address")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> EmailStr:
        if value is None:
            raise ValueError("Email cannot be null")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str:
        if value is None or PHONE_PATTERN.fullmatch(value) is None:
            raise ValueError("Invalid phone number")
        return value

    @field_validator("delivery_fee", mode="before")
    @classmethod
    def validate_delivery_fee(cls, value: object) -> int:
        if type(value) is not int or value < 0:
            raise ValueError("Invalid delivery fee")
        return value


class StoreResponse(BaseModel):
    id: str
    store_name: str = Field(validation_alias="name")
    address: str
    email: EmailStr
    phone_number: str
    delivery_fee: int

    model_config = ConfigDict(from_attributes=True)


class StoreItemResponse(BaseModel):
    id: str
    item_name: str = Field(validation_alias="name")
    price: int
    stock: int

    model_config = ConfigDict(from_attributes=True)