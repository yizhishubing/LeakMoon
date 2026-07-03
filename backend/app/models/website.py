"""
网站模型
作用：管理被巡检的所有校园网站，包括 URL、爬取策略、状态等信息
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.database import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="网站名称")
    url = Column(String(500), unique=True, nullable=False, comment="目标URL")
    depth = Column(Integer, default=2, comment="爬取深度（0=仅首页）")
    max_pages = Column(Integer, default=100, comment="最大爬取页数")
    crawl_interval = Column(Integer, default=24, comment="爬取间隔(小时)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Website {self.name}>"
