from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    leak_record_id: int
    sent_at: Optional[datetime] = None
    channel: str
    status: str
    recipient: str
    content: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
