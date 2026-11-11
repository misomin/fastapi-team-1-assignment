from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from wapang.common.exceptions import InvalidFormatException

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password", mode="after")
    def validate_password(cls, v) -> str:
        if len(v) < 8 or len(v) > 20:
            raise InvalidFormatException()
        return v

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    nickname: str | None
    address: str | None
    phone_number: str | None
    
    model_config = ConfigDict(from_attributes=True)
