from __future__ import annotations

from pathlib import Path

from pydantic import BaseSettings


def _get_project_root() -> Path:
    """获取项目根目录"""
    # 获取 backend/app 目录
    backend_app_dir = Path(__file__).parent.parent.resolve()
    # 获取 backend 目录
    backend_dir = backend_app_dir.parent.resolve()
    # 获取项目根目录
    return backend_dir.parent.resolve()


def _get_database_url() -> str:
    """获取数据库的绝对路径 URL"""
    project_root = _get_project_root()
    db_path = project_root / "data" / "doc_intelli_fix.db"
    return f"sqlite:///{db_path.as_posix()}"


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"

    APP_NAME: str = "Visson Pro"
    
    # JWT_SECRET 配置说明：
    # 1. 优先从 .env 文件读取（推荐在生产环境使用）
    # 2. 如果没有 .env 文件，使用固定的默认值（开发环境）
    # 3. 重要：一旦设置，不要随意更改，否则所有已发放的 token 会失效
    JWT_SECRET: str = "visson-pro-secret-key-change-in-production-2024"
    JWT_EXPIRE_MINUTES: int = 0  # 0 表示永不过期（100 年）

    # 使用绝对路径存储数据库，避免路径混乱
    # 数据库统一存放在项目根目录的 data 文件夹
    DATABASE_URL: str = _get_database_url()
    DATA_DIR: str = (_get_project_root() / "data").as_posix()
    
    # 存储目录
    STORAGE_DIR: str = (_get_project_root() / "storage").as_posix()

    # Qwen 大模型配置
    # 方式一：使用 QWEN_API_URL（兼容旧配置）
    QWEN_API_URL: str = ""
    
    # 方式二：使用 LLM_API_BASE + LLM_API_KEY（推荐，DashScope 兼容格式）
    LLM_API_BASE: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "qwen3.6-plus"


settings = Settings()


def storage_root() -> Path:
    return Path(settings.STORAGE_DIR)


def data_root() -> Path:
    """获取数据目录的绝对路径（项目根目录/data）"""
    return Path(settings.DATA_DIR)


def database_path() -> Path:
    """获取数据库文件的绝对路径"""
    return data_root() / "doc_intelli_fix.db"
