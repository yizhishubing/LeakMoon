"""
仪表盘 API
作用：提供风险仪表盘的聚合统计数据
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.database import get_db
from app.models.leak import LeakRecord
from app.models.alert import AlertLog, AlertStatus
from app.models.website import Website

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    获取仪表盘统计卡片数据

    返回：
        active_websites: 启用的巡检网站数
        total_leaks: 累计发现泄露总数
        high_risk_leaks: 高风险泄露数
        pending_alerts: 待处理告警数（pending/sent 状态的告警）
    """
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
    """
    获取泄露类型分布数据（用于饼图）

    返回：
        [{name: str, value: int}, ...]
    """
    results = (
        db.query(LeakRecord.data_type, func.count(LeakRecord.id))
        .group_by(LeakRecord.data_type)
        .all()
    )
    return [{"name": r[0], "value": r[1]} for r in results]


@router.get("/leak-trend")
def get_leak_trend(days: int = 7, db: Session = Depends(get_db)):
    """
    获取近 N 天的泄露趋势数据（用于折线图）

    返回：
        {dates: [str], counts: [int]}
    """
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
    """
    获取各网站的风险等级分布数据（用于堆叠柱状图）

    返回：
        [{name: str, high: int, medium: int, low: int}, ...]
    """
    results = (
        db.query(
            Website.name,
            func.sum(func.if_(LeakRecord.severity == "high", 1, 0)).label("high"),
            func.sum(func.if_(LeakRecord.severity == "medium", 1, 0)).label("medium"),
            func.sum(func.if_(LeakRecord.severity == "low", 1, 0)).label("low"),
        )
        .outerjoin(LeakRecord, Website.id == LeakRecord.website_id)
        .group_by(Website.id, Website.name)
        .all()
    )

    return [
        {
            "name": r[0],
            "high": r[1] or 0,
            "medium": r[2] or 0,
            "low": r[3] or 0,
        }
        for r in results
    ]
