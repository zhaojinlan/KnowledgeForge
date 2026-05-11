from qdrant_client import QdrantClient

# 连接本地 Qdrant
client = QdrantClient(url="http://localhost:6333",api_key="123456")

# 指定你要查看的 collection 名称
collection_name = "document_embeddings"  # ❗请替换为你的实际 collection 名

# 检查 collection 是否存在
try:
    collection_info = client.get_collection(collection_name)
    print(f"✅ Collection '{collection_name}' 存在")
    print(f"📊 向量数量: {collection_info.points_count}")
    print(f"🔬 向量维度: {collection_info.config.params.vectors.size}")
    print(f"🎯 距离算法: {collection_info.config.params.vectors.distance}")
except Exception as e:
    print(f"❌ 错误：collection '{collection_name}' 不存在或连接失败。")
    print(e)
    exit()

# 读取向量数据（最多前 5 条，可调）
print("\n🔍 正在读取向量数据...")
points, _ = client.scroll(
    collection_name=collection_name,
    limit=5,
    with_vectors=True,    # 包含向量
    with_payload=True,    # 包含元数据
)

print("\n📋 数据列表：")
for point in points:
    print(f"ID: {point.id}")
    print(f"向量: {point.vector}")
    if point.payload:
        print(f"元数据: {point.payload}")
    print("-" * 40)
