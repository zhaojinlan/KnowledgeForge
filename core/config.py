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
    chunk_overlap:int = 100
    chunk_size:int = 800
    # 应用配置
    app_name: str = "Model Server"
    debug: bool = False

    # CORS 配置（逗号分隔的源列表，或 "*" 表示全部）
    cors_origins: str = "*"

    # MinIO 配置
    minio_endpoint: str = "localhost:19000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_name: str = "rag-files"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="forbid"
    )
# 创建全局 settings 实例
try:
    settings = Settings()
    print("Config loaded successfully!")
except Exception as e:
    print("Config loading failed! Possible reasons:")
    print("   1. .env file not found or path is wrong")
    print("   2. Missing required fields in .env")
    print("   3. Invalid field values (e.g. qdrant_port is a string)")
    print("\nDetailed error:")
    raise e