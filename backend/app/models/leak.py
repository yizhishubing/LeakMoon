"""
泄露记录模型
作用：记录每次检测发现的敏感信息泄露，包含匹配详情、严重程度、上下文等
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class LeakRecord(Base):
    __tablename__ = "leak_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    detected_at = Column(DateTime, server_default=func.now())
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=True, comment="命中的检测规则ID")
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    severity = Column(String(20), nullable=False, comment="严重程度: high/medium/low")
    data_type = Column(String(100), nullable=False, comment="数据类型: id_card, phone, student_id...")
    matched_text = Column(Text, nullable=False, comment="匹配到的原文片段（脱敏处理）")
    source_url = Column(String(500), nullable=False, comment="泄露页面的URL")
    context_before = Column(String(500), comment="上下文前缀")
    context_after = Column(String(500), comment="上下文后缀")
    is_verified = Column(Integer, default=0, comment="0=未确认, 1=已确认, 2=误报")
    verified_by = Column(String(100), nullable=True, comment="确认人")
    verified_at = Column(DateTime, nullable=True, comment="确认时间")
    note = Column(Text, nullable=True, comment="备注")

    def __repr__(self):
        return f"<LeakRecord {self.data_type} on {self.source_url}>"
