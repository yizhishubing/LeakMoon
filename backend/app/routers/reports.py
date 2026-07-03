"""
报表管理 API（占位）
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_reports():
    """获取报表列表"""
    return {"message": "报表功能开发中", "reports": []}
