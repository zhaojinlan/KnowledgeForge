from qdrant_client import QdrantClient
import os

# 从环境变量读取配置（由 .env 提供）
host = os.getenv("QDRANT_HOST", "localhost")
port = os.getenv("QDRANT_PORT", "8333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=f"http://{host}:{port}", api_key=api_key)

# 指定你要查看的 collection 名称
collection_name = "document_embeddings"

# 检查 collection 是否存在
try:
    collection_info = client.get_collection(collection_name)
    print(f"Collection '{collection_name}' exists")
    print(f"  Point count: {collection_info.points_count}")
    print(f"  Vector dim: {collection_info.config.params.vectors.size}")
    print(f"  Distance: {collection_info.config.params.vectors.distance}")
except Exception as e:
    print(f"Error: collection '{collection_name}' not found or connection failed.")
    print(e)
    exit()

# 读取向量数据（最多前 5 条）
print("\nReading vector data...")
points, _ = client.scroll(
    collection_name=collection_name,
    limit=5,
    with_vectors=True,
    with_payload=True,
)

print("\nData list:")
for point in points:
    print(f"ID: {point.id}")
    print(f"Vector: {point.vector}")
    if point.payload:
        print(f"Payload: {point.payload}")
    print("-" * 40)
