from datetime import datetime

from pydantic import BaseModel, Field


class AutomationRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    trigger: str = Field(min_length=2, max_length=160)
    condition: str = Field(min_length=2, max_length=240)
    action: str = Field(min_length=2, max_length=240)
    enabled: bool = True


class AutomationRuleUpdate(BaseModel):
    name: str | None = None
    trigger: str | None = None
    condition: str | None = None
    action: str | None = None
    enabled: bool | None = None


class AutomationRuleOut(AutomationRuleCreate):
    id: int

    model_config = {"from_attributes": True}


class AutomationEventOut(BaseModel):
    id: int
    rule_id: int | None
    job_id: int | None
    message: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
