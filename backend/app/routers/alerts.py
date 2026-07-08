"""
告警管理 API
作用：查询告警列表、确认/处理告警
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.alert import AlertLog, AlertStatus
from app.models.leak import LeakRecord
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    skip: int = 0,
    limit: int = 30,
    status: str = "",
    db: Session = Depends(get_db),
):
    """
    获取告警列表（分页 + 按时间倒序 + 可选状态筛选）

    参数：
        skip: 跳过记录数
        limit: 每页数量，默认30
        status: 按状态筛选（可选）
    """
    query = db.query(AlertLog).order_by(AlertLog.sent_at.desc())
    if status:
        query = query.filter(AlertLog.status == status)
    return query.offset(skip).limit(limit).all()


@router.put("/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """确认告警：将状态从 SENT 改为 ACKNOWLEDGED"""
    alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    alert.status = AlertStatus.ACKNOWLEDGED
    db.commit()
    return {"message": "告警已确认"}


@router.put("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """处理告警：将状态改为 RESOLVED"""
    alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    alert.status = AlertStatus.RESOLVED
    db.commit()
    return {"message": "告警已处理"}


@router.get("/total")
def get_alert_total(status: str = "", db: Session = Depends(get_db)):
    """获取告警总数（用于分页）"""
    query = db.query(func.count(AlertLog.id))
    if status:
        query = query.filter(AlertLog.status == status)
    return {"total": query.scalar()}
