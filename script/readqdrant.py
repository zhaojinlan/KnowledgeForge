from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

# 从环境变量读取配置（由 .env 提供）
host = os.getenv("QDRANT_HOST", "localhost")
port = os.getenv("QDRANT_PORT", "8333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=f"http://{host}:{port}", api_key=api_key)

collection_name = "document_embeddings"

# 如果集合已存在，先删除
if client.collection_exists(collection_name=collection_name):
    print(f"Collection '{collection_name}' already exists, deleting...")
    client.delete_collection(collection_name=collection_name)
    print("Old collection deleted.")

# 创建新的集合
try:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1024,
            distance=models.Distance.COSINE
        ),
    )
    print(f"Created Qdrant collection: {collection_name}")
except Exception as e:
    print(f"Failed to create collection: {e}")
