"""
泄露记录 API
作用：查询泄露记录列表、确认/误报标记
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.leak import LeakRecord
from app.schemas.leak import LeakResponse
import re

# Unicode 代理对及替换字符：确保 API 响应 JSON 序列化不报错
_SANITIZE_RE = re.compile(r'[\ud800-\udfff�]')


def _clean_str(s: str) -> str:
    """清理字符串中的非法 Unicode 字符（防御性处理，防止 JSON 序列化异常）"""
    if not s:
        return s
    return _SANITIZE_RE.sub('', s)


def _clean_record(record: LeakRecord) -> LeakRecord:
    """对泄露记录各文本字段进行 Unicode 清洗（防御性清洗，确保 JSON 可序列化）"""
    for field in ['rule_name', 'matched_text', 'source_url', 'context_before', 'context_after', 'note']:
        val = getattr(record, field)
        if val:
            setattr(record, field, _clean_str(val))
    return record

router = APIRouter()


@router.get("/", response_model=list[LeakResponse])
def list_leaks(
    skip: int = 0,
    limit: int = 30,
    search: str = "",
    db: Session = Depends(get_db),
):
    """
    获取泄露记录列表（分页 + 搜索 + 按检测时间倒序）

    参数：
        skip: 跳过记录数
        limit: 每页数量，默认30
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
    records = query.order_by(LeakRecord.detected_at.desc()).offset(skip).limit(limit).all()
    # 防御性清洗：确保所有文本字段无非法 Unicode 字符，防止 JSON 序列化异常
    return [_clean_record(r) for r in records]


@router.get("/total")
def get_leak_total(search: str = "", db: Session = Depends(get_db)):
    """获取泄露记录总数（用于分页）"""
    query = db.query(func.count(LeakRecord.id))
    if search:
        query = query.filter(
            or_(
                LeakRecord.source_url.contains(search),
                LeakRecord.data_type.contains(search),
            )
        )
    return {"total": query.scalar()}


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
