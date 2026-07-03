"""
配置管理模块
作用：集中读取环境变量和配置项
做法：使用 pydantic-settings 读取 .env 文件中的配置
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:root123456@localhost:3306/leakmoon"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 安全密钥
    SECRET_KEY: str = "leakmoon-dev-secret-key"

    # 告警邮件配置
    ALERT_EMAIL_HOST: str = "smtp.qq.com"
    ALERT_EMAIL_PORT: int = 465
    ALERT_EMAIL_USER: str = ""
    ALERT_EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = ""
    ALERT_EMAIL_TO: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
