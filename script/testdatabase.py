# test_databases.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# =============================
# MongoDB 测试
# =============================
def test_mongodb():
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("❌ MongoDB URI 未设置！请检查 .env 文件")
        return False

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB 连接成功！")

        # 测试认证（列出数据库）
        dbs = client.list_database_names()
        print(f"📊 MongoDB 数据库列表: {dbs[:5]} {'...' if len(dbs) > 5 else ''}")

        # 写入测试数据
        test_db = client["test_db"]
        test_col = test_db["test_collection"]
        test_col.insert_one({"test": "hello mongo", "ts": 1})
        print("📝 MongoDB 写入测试数据成功")

        client.close()
        return True

    except ServerSelectionTimeoutError:
        print("❌ MongoDB 连接超时，请检查服务是否运行（docker ps）")
        return False
    except OperationFailure as e:
        if "Authentication" in str(e):
            print("❌ MongoDB 认证失败！请检查用户名/密码")
        else:
            print(f"❌ MongoDB 认证错误: {e}")
        return False
    except Exception as e:
        print(f"❌ MongoDB 其他错误: {e}")
        return False


# =============================
# Qdrant 测试
# =============================
def test_qdrant():
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.exceptions import ApiException
    import os

    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", 8333))
    api_key = os.getenv("QDRANT_API_KEY")

    try:
        # ✅ 正确初始化：强制使用 HTTP
        client = QdrantClient(
            url=f"http://{host}:{port}",
            api_key=api_key,
            timeout=10
        )

        # ✅ 测试连接
        try:
            client.get_collections()
            print("✅ Qdrant 连接成功！服务可达")
        except ApiException as e:
            print(f"❌ Qdrant API 错误: {e}")
            return False

        collection_name = "test_collection"

        # ✅ 替代 recreate_collection：先删除再创建（或检查后创建）
        try:
            client.delete_collection(collection_name)
            print(f"🗑️ 旧集合 '{collection_name}' 已删除")
        except:
            pass  # 集合不存在也正常

        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE)
        )
        print("📝 Qdrant 创建测试集合成功")

        # ✅ 插入向量
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"name": "vec1"}),
                models.PointStruct(id=2, vector=[0.5, 0.6, 0.7, 0.8], payload={"name": "vec2"}),
            ]
        )
        print("📥 Qdrant 插入向量成功")

        # ✅ 搜索：使用 search() 方法（注意参数位置）
        # 🔥 关键：search 是 client 的方法，但必须传 collection_name
        results = client.query_points(
            collection_name=collection_name,
            query=[0.1, 0.2, 0.3, 0.4],
            limit=2
        )
        print("🔍 Qdrant 搜索成功，结果:")
        for hit in results.points:
            print(f"  - ID: {hit.id}, 匹配: {hit.payload['name']}, 相似度: {hit.score:.3f}")

        return True

    except Exception as e:
        print(f"❌ Qdrant 错误: {e}")
        return False



# =============================
# 主函数
# =============================
if __name__ == "__main__":
    print("🚀 开始测试数据库连接...\n")

    print("1. 测试 MongoDB...")
    mongo_ok = test_mongodb()
    print()

    print("2. 测试 Qdrant...")
    qdrant_ok = test_qdrant()
    print()

    # 总结
    if mongo_ok and qdrant_ok:
        print("🎉 所有数据库测试通过！你的 knowledgeforZJl 环境正常运行！")
    else:
        print("💥 有一个或多个数据库测试失败，请检查：")
        if not mongo_ok:
            print("   - MongoDB: 检查 docker 是否运行、密码是否正确")
        if not qdrant_ok:
            print("   - Qdrant: 检查 api-key、端口、服务是否启动")

        print("\n💡 提示：运行 `docker ps` 查看容器状态")
