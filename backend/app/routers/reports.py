"""
报表管理 API
作用：查询报表列表、生成报表
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.report import Report
from app.models.leak import LeakRecord
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/")
def list_reports(db: Session = Depends(get_db)):
    """获取报表列表"""
    return db.query(Report).order_by(Report.generated_at.desc()).all()


@router.post("/")
def generate_report(data: dict, db: Session = Depends(get_db)):
    """
    生成巡检报表

    参数：
        data: {"title": str, "report_type": "daily/weekly/monthly/custom"}
    """
    title = data.get("title", f"巡检报表_{datetime.now().strftime('%Y%m%d_%H%M')}")
    report_type = data.get("report_type", "custom")

    # 统计数据
    total_leaks = db.query(LeakRecord).count()
    high_count = db.query(LeakRecord).filter(LeakRecord.severity == "high").count()
    medium_count = db.query(LeakRecord).filter(LeakRecord.severity == "medium").count()
    low_count = db.query(LeakRecord).filter(LeakRecord.severity == "low").count()

    summary = (
        f"本次巡检共发现 {total_leaks} 条泄露记录，"
        f"其中高风险 {high_count} 条，中风险 {medium_count} 条，低风险 {low_count} 条。"
    )

    report = Report(
        title=title,
        report_type=report_type,
        summary=summary,
        status="generated",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "summary": report.summary,
        "generated_at": report.generated_at.isoformat(),
    }
