"""
规则管理 API
"""

from fastapi import APIRouter
from app.services.rule_engine import RuleEngine

router = APIRouter()


@router.get("/")
def list_rules():
    """获取所有检测规则"""
    engine = RuleEngine()
    return engine.get_all_rules()


@router.post("/reload")
def reload_rules():
    """重新加载 YAML 规则文件"""
    engine = RuleEngine()
    engine.reload()
    return {"message": "规则已重新加载"}
