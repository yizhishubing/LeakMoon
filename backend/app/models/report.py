"""
报表模型
作用：记录生成的巡检报表，支持历史回溯
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    report_type = Column(String(50), nullable=False, comment="daily/weekly/monthly/custom")
    generated_at = Column(DateTime, server_default=func.now())
    file_path = Column(String(500), nullable=True, comment="生成的报表文件路径")
    summary = Column(Text, nullable=True, comment="报表摘要")
    status = Column(String(20), default="pending", comment="pending/generated/failed")

    def __repr__(self):
        return f"<Report {self.title}>"
