"""
告警管理 API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alert import AlertLog
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
def list_alerts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """获取告警列表（分页）"""
    return db.query(AlertLog).offset(skip).limit(limit).all()
