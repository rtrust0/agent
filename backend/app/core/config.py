from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """集中配置：缺失必填项时启动即失败（fail fast）。"""

    APP_NAME: str = "辰光Agent RBAC Backend"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./rbac.db"

    JWT_SECRET: str = "change-me-in-production-change-me-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
