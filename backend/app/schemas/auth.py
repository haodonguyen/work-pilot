from pydantic import BaseModel, EmailStr, Field


class BusinessOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RegisterIn(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    business: BusinessOut

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
