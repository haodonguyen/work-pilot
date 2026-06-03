from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    name: str | None = Field(default=None, min_length=2, max_length=200)


class CustomerOut(CustomerBase):
    id: int

    model_config = {"from_attributes": True}
