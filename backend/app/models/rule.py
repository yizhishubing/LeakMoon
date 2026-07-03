"""
检测规则模型
作用：存储可配置的检测规则，支持通过 YAML 文件批量导入
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.database import Base


class DetectionRule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="规则名称")
    pattern = Column(Text, nullable=False, comment="正则表达式")
    data_type = Column(String(100), nullable=False, comment="数据类型标识")
    severity = Column(String(20), default="medium", comment="严重程度: high/medium/low")
    description = Column(Text, nullable=True, comment="规则描述")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DetectionRule {self.name}>"
