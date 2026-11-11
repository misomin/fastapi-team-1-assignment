from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import re

from wapang.common.exceptions import InvalidFormatException

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password", mode="after")
    def validate_password(cls, v) -> str:
        if len(v) < 8 or len(v) > 20:
            raise InvalidFormatException()
        return v

class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    address: str | None = None
    phone_number: str | None = None

    @field_validator("nickname")
    def validate_nickname(cls, value: str | None) -> str:
        if value is None or len(value) > 20:
            raise InvalidFormatException()
        return value

    @field_validator("address")
    def validate_address(cls, value: str | None) -> str:
        if value is None or len(value) > 100:
            raise InvalidFormatException()
        return value

    @field_validator("phone_number")
    def validate_phone_number(cls, value: str | None) -> str:
        if value is None or re.fullmatch(r"010-\d{4}-\d{4}", value) is None:
            raise InvalidFormatException()
        return value

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    nickname: str | None
    address: str | None
    phone_number: str | None
    
    model_config = ConfigDict(from_attributes=True)
