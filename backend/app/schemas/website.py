from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WebsiteCreate(BaseModel):
    name: str
    url: str
    depth: int = 2
    max_pages: int = 100
    crawl_interval: int = 24


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    depth: Optional[int] = None
    max_pages: Optional[int] = None
    crawl_interval: Optional[int] = None
    is_active: Optional[bool] = None


class WebsiteResponse(BaseModel):
    id: int
    name: str
    url: str
    depth: int
    max_pages: int
    crawl_interval: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
