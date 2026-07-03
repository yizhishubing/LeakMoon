from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeakResponse(BaseModel):
    id: int
    website_id: int
    detected_at: Optional[datetime] = None
    rule_name: str
    severity: str
    data_type: str
    matched_text: str
    source_url: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    is_verified: int
    note: Optional[str] = None

    model_config = {"from_attributes": True}
