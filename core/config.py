# core/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

class Settings(BaseSettings):
    model: str
    api_key: str
    base_url: str

    # 显式指定 .env 路径
    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8"
    )

settings = Settings()