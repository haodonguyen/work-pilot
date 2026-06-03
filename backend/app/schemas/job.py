from datetime import datetime

from pydantic import BaseModel, Field

from app.models import JobStatus
from app.schemas.customer import CustomerOut


class JobBase(BaseModel):
    customer_id: int
    service_type: str = Field(min_length=2, max_length=160)
    scheduled_at: datetime
    price: float = Field(ge=0)
    status: JobStatus = JobStatus.scheduled
    staff_member: str | None = None
    notes: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    customer_id: int | None = None
    service_type: str | None = Field(default=None, min_length=2, max_length=160)
    scheduled_at: datetime | None = None
    price: float | None = Field(default=None, ge=0)
    status: JobStatus | None = None
    staff_member: str | None = None
    notes: str | None = None


class JobOut(JobBase):
    id: int
    customer: CustomerOut

    model_config = {"from_attributes": True}
