"""
泄露记录 API
作用：查询泄露记录列表、确认/误报标记
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.leak import LeakRecord
from app.schemas.leak import LeakResponse

router = APIRouter()


@router.get("/", response_model=list[LeakResponse])
def list_leaks(skip: int = 0, limit: int = 50, search: str = "", db: Session = Depends(get_db)):
    """
    获取泄露记录列表（分页 + 搜索）

    参数：
        skip: 跳过记录数
        limit: 每页数量
        search: 搜索关键词（匹配 URL 或类型）
    """
    query = db.query(LeakRecord)
    if search:
        query = query.filter(
            or_(
                LeakRecord.source_url.contains(search),
                LeakRecord.data_type.contains(search),
            )
        )
    return query.offset(skip).limit(limit).all()


@router.put("/{leak_id}/verify")
def verify_leak(leak_id: int, data: dict, db: Session = Depends(get_db)):
    """
    确认/误报标记

    参数：
        leak_id: 泄露记录 ID
        data: {"is_verified": 1} 确认 或 {"is_verified": 2, "note": "误报原因"}
    """
    leak = db.query(LeakRecord).filter(LeakRecord.id == leak_id).first()
    if not leak:
        raise HTTPException(status_code=404, detail="泄露记录不存在")

    leak.is_verified = data.get("is_verified", 0)
    if "note" in data:
        leak.note = data["note"]
    db.commit()
    return {"message": "已更新"}
