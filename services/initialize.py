"""
initialize_stores.py
独立的数据库与向量库初始化脚本。
功能：检查 MongoDB 和 Qdrant 的连接，确保集合/库存在，不存在则创建。
"""
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from pymongo import MongoClient

from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_qdrant():
    """初始化 Qdrant，确保集合存在"""
    try:
        client = QdrantClient(
            url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
            api_key=settings.qdrant_api_key,
            timeout=10
        )
        
        collection_name = settings.qdrant_collection_name
        embedding_dim = settings.embedding_dim
        
        # 检查集合是否存在
        if client.collection_exists(collection_name):
            logger.info(f"✅ Qdrant 集合 '{collection_name}' 已存在。")
        else:
            # 创建集合
            client.create_collection(
                collection_name=collection_name,
                vectors_config=rest_models.VectorParams(
                    size=embedding_dim,
                    distance=rest_models.Distance.COSINE
                ),
            )
            logger.info(f"✅ 成功创建 Qdrant 集合 '{collection_name}'。")
            
        return client
    except Exception as e:
        logger.error(f"❌ Qdrant 初始化失败: {e}")
        raise

def initialize_mongodb():
    """初始化 MongoDB，确保数据库和集合存在（并可选地创建索引）"""
    try:
        client = MongoClient(settings.mongodb_uri)
        db = client[settings.mongo_db_name]
        collection = db[settings.mongo_text_collection]
        
        # 检查集合是否存在
        if settings.mongo_text_collection in db.list_collection_names():
            logger.info(f"✅ MongoDB 集合 '{settings.mongo_text_collection}' 已存在。")
        else:
            # 显式创建集合
            db.create_collection(settings.mongo_text_collection)
            logger.info(f"✅ 成功创建 MongoDB 集合 '{settings.mongo_text_collection}'。")
            
        # 可选：为 _id 创建索引以提高检索速度
        # collection.create_index([("_id", 1)])
        
        return client
    except Exception as e:
        logger.error(f"❌ MongoDB 初始化失败: {e}")
        raise

def main():
    print("🚀 开始初始化数据存储环境...")
    mongo_client = None
    qdrant_client = None
    
    try:
        mongo_client = initialize_mongodb()
        qdrant_client = initialize_qdrant()
        print("🎉 环境初始化完成！数据库与向量库均已就绪。")
    except Exception as e:
        print(f" 初始化过程中发生错误: {e}")
        exit(1)
    finally:
        if mongo_client:
            mongo_client.close()
        if qdrant_client:
            # 注意：QdrantClient 可能没有直接的 close，取决于版本
            pass

if __name__ == "__main__":
    main()