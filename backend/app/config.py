"""
配置管理模块
作用：集中读取环境变量和配置项
做法：使用 pydantic-settings 读取 .env 文件中的配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:root123456@localhost:3306/leakmoon"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "leakmoon-dev-secret-key"

    ALERT_EMAIL_HOST: str = "smtp.qq.com"
    ALERT_EMAIL_PORT: int = 465
    ALERT_EMAIL_USER: str = ""
    ALERT_EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = ""
    ALERT_EMAIL_TO: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
