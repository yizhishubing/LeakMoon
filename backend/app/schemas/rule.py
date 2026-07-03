from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RuleResponse(BaseModel):
    id: int
    name: str
    pattern: str
    data_type: str
    severity: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
