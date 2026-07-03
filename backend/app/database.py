"""
数据库连接模块
作用：创建数据库引擎、会话工厂、声明基类
做法：从 config 读取数据库 URL，使用 SQLAlchemy 连接 MySQL
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # 连接前检测有效性
    pool_recycle=3600,     # 连接回收时间（秒）
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """依赖注入：为每个请求提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
