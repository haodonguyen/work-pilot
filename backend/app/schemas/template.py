from pydantic import BaseModel, Field

from app.models import TemplateType


class MessageTemplateCreate(BaseModel):
    type: TemplateType
    name: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=5)


class MessageTemplateUpdate(BaseModel):
    type: TemplateType | None = None
    name: str | None = None
    body: str | None = None


class MessageTemplateOut(MessageTemplateCreate):
    id: int

    model_config = {"from_attributes": True}
