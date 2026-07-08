"""
仪表盘 API
作用：提供风险仪表盘的聚合统计数据
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models.leak import LeakRecord
from app.models.alert import AlertLog, AlertStatus
from app.models.website import Website

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    active_websites = db.query(Website).filter(Website.is_active == True).count()
    total_leaks = db.query(func.count(LeakRecord.id)).scalar()
    high_risk_leaks = db.query(func.count(LeakRecord.id)).filter(LeakRecord.severity == "high").scalar()
    pending_alerts = db.query(func.count(AlertLog.id)).filter(
        AlertLog.status.in_([AlertStatus.PENDING, AlertStatus.SENT])
    ).scalar()

    return {
        "activeWebsites": active_websites,
        "totalLeaks": total_leaks,
        "highRiskLeaks": high_risk_leaks,
        "pendingAlerts": pending_alerts,
    }


@router.get("/leak-types")
def get_leak_types(db: Session = Depends(get_db)):
    results = (
        db.query(LeakRecord.data_type, func.count(LeakRecord.id))
        .group_by(LeakRecord.data_type)
        .all()
    )
    return [{"name": r[0], "value": r[1]} for r in results]


@router.get("/leak-trend")
def get_leak_trend(days: int = 7, db: Session = Depends(get_db)):
    now = datetime.now()
    dates = []
    counts = []

    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        date_str = day.strftime("%m-%d")
        count = (
            db.query(func.count(LeakRecord.id))
            .filter(LeakRecord.detected_at >= start, LeakRecord.detected_at <= end)
            .scalar()
        )

        dates.append(date_str)
        counts.append(count)

    return {"dates": dates, "counts": counts}


@router.get("/risk-map")
def get_risk_map(db: Session = Depends(get_db)):
    results = (
        db.query(
            Website.name,
            func.coalesce(func.sum(func.if_(LeakRecord.severity == "high", 1, 0)), 0).label("high"),
            func.coalesce(func.sum(func.if_(LeakRecord.severity == "medium", 1, 0)), 0).label("medium"),
            func.coalesce(func.sum(func.if_(LeakRecord.severity == "low", 1, 0)), 0).label("low"),
        )
        .outerjoin(LeakRecord, Website.id == LeakRecord.website_id)
        .group_by(Website.id, Website.name)
        .all()
    )

    return [
        {
            "name": r[0],
            "high": int(r[1]),
            "medium": int(r[2]),
            "low": int(r[3]),
        }
        for r in results
    ]
