from datetime import date

from pydantic import BaseModel, Field

from app.models import InvoiceStatus
from app.schemas.customer import CustomerOut


class InvoiceBase(BaseModel):
    customer_id: int
    number: str = Field(min_length=2, max_length=80)
    amount: float = Field(ge=0)
    due_date: date
    status: InvoiceStatus = InvoiceStatus.draft
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    customer_id: int | None = None
    number: str | None = Field(default=None, min_length=2, max_length=80)
    amount: float | None = Field(default=None, ge=0)
    due_date: date | None = None
    status: InvoiceStatus | None = None
    notes: str | None = None


class InvoiceOut(InvoiceBase):
    id: int
    customer: CustomerOut

    model_config = {"from_attributes": True}
