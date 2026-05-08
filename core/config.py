from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os


class Settings(BaseSettings):
    # LLM 配置
    model: str
    api_key: str
    base_url: str

    # MongoDB 配置
    mongo_root_username: str
    mongo_root_password: str
    mongodb_uri: str  # 会自动从 MONGODB_URI 读取（Pydantic 自动转换）

    # Qdrant 配置
    qdrant_host: str
    qdrant_port: int
    qdrant_api_key: str

    # 应用配置
    app_name: str = "Model Server"
    debug: bool = False

    # ✅ 正确配置 .env 路径
    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="forbid" 
    )


# 创建全局 settings 实例
settings = Settings()