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
    mongodb_uri: str
    mongo_db_name: str = "document_db"
    mongo_text_collection: str = "text_contents"
    
    # Qdrant 配置
    qdrant_host: str
    qdrant_port: int
    qdrant_api_key: str
    qdrant_collection_name: str = "document_embeddings"
    
    # Embedding 配置
    embedding_model: str
    embedding_api_key: str
    embedding_base_url: str
    embedding_dim: int = 1024
    
    # 应用配置
    app_name: str = "Model Server"
    debug: bool = False
    
    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="forbid"
    )
# 创建全局 settings 实例
try:
    settings = Settings()
    print("✅ 全局配置加载成功！")
except Exception as e:
    print("❌ 配置加载失败！可能是以下原因：")
    print("   1. .env 文件不存在或路径错误")
    print("   2. .env 中缺少必要的字段（如 embedding_model、api_key 等）")
    print("   3. 字段值为空或格式错误（如 qdrant_port 写成了字符串）")
    print("\n🎯 详细错误信息：")
    raise e  # 重新抛出异常，便于定位