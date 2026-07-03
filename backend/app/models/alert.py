"""
告警日志模型
作用：追踪告警的发送状态，确保告警可靠送达并可追溯
"""

from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AlertStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    leak_record_id = Column(BigInteger, ForeignKey("leak_records.id"), nullable=False, index=True)
    sent_at = Column(DateTime, server_default=func.now())
    channel = Column(String(50), nullable=False, comment="notification_channel: email/in_site")
    status = Column(SAEnum(AlertStatus), default=AlertStatus.PENDING)
    recipient = Column(String(200), nullable=False, comment="接收者")
    content = Column(Text, nullable=False, comment="告警内容摘要")
    error_message = Column(Text, nullable=True, comment="发送失败时的错误信息")

    def __repr__(self):
        return f"<AlertLog {self.channel} -> {self.recipient}>"
