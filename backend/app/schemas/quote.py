from datetime import date

from pydantic import BaseModel, Field

from app.models import QuoteStatus
from app.schemas.customer import CustomerOut


class QuoteBase(BaseModel):
    customer_id: int
    number: str = Field(min_length=2, max_length=80)
    service_type: str = Field(min_length=2, max_length=160)
    amount: float = Field(ge=0)
    valid_until: date
    status: QuoteStatus = QuoteStatus.draft
    notes: str | None = None


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    customer_id: int | None = None
    number: str | None = Field(default=None, min_length=2, max_length=80)
    service_type: str | None = Field(default=None, min_length=2, max_length=160)
    amount: float | None = Field(default=None, ge=0)
    valid_until: date | None = None
    status: QuoteStatus | None = None
    notes: str | None = None


class QuoteOut(QuoteBase):
    id: int
    customer: CustomerOut

    model_config = {"from_attributes": True}
