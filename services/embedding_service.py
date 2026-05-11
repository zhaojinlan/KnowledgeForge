# services/embedding_service.py
"""
这个文件提供文本向量化的一个类

"""
from typing import List, Any
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from core.config import settings
import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.database import Database
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from core.config import settings
import os
import uuid
import logging
import codecs
import asyncio
from datetime import datetime
class EmbeddingService:
    """
    封装支持 OpenAI API 兼容接口的远程 Embedding 服务
    适用于本地部署的 bge-m3、text-embedding-inference、vLLM 等
    使用 LlamaIndex 的 OpenAIEmbedding 客户端适配任意 OpenAI-like 接口
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        # 设置环境变量（可选）
        os.environ["OPENAI_API_KEY"] = api_key or "dummy"
        os.environ["OPENAI_API_BASE"] = base_url

        # 初始化 OpenAIEmbedding
        self.embedding_model: BaseEmbedding = OpenAIEmbedding(
            model_name=model,
            _api_key_in_kwargs=True,
            api_base=base_url,
            api_key=api_key or "dummy",
            embed_batch_size=10,
            timeout=30,
            additional_kwargs={},
            # 可根据需要调整 worker 数量（用于异步并发）
            num_workers=4,
        )

        # Monkey patch: 绕过 OpenAIEmbeddingModelType 枚举校验
        def _get_model_enum(self_, model: str):
            return model

        self.embedding_model._get_model_enum = _get_model_enum.__get__(
            self.embedding_model, OpenAIEmbedding
        )

    def get_embedding(self, text: str) -> List[float]:
        """同步：获取单个文本的 embedding"""
        return self.embedding_model.get_text_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """同步：批量获取多个文本的 embedding"""
        return self.embedding_model.get_text_embedding_batch(texts)

    async def aget_embedding(self, text: str) -> List[float]:
        """异步：获取单个文本的 embedding"""
        result = await self.embedding_model.aget_text_embedding(text)
        return result

    async def aget_embeddings(self, texts: List[str]) -> List[List[float]]:
        """异步：批量获取多个文本的 embedding"""
        result = await self.embedding_model.aget_text_embedding_batch(
            texts,
            show_progress=False,  # 可根据需要开启s
        )
        return result  # List[List[float]]

# ✅ 创建并导出单例服务 
embedding_service = EmbeddingService( model=settings.embedding_model, api_key=settings.embedding_api_key, base_url=settings.embedding_base_url) 

 
 

# 配置日志
logger = logging.getLogger(__name__)
 

# ================= 改进后的文档存储服务 =================
class DocumentStorageService:
    """
    处理文档读取、向量化及双库存储的核心服务
    
    使用 llama_index 的 SentenceSplitter 进行智能分块，
    并异步调用 EmbeddingService 生成向量
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        qdrant_host: str,
        qdrant_port: int,
        qdrant_api_key: str,
        qdrant_collection: str,
        embedding_dim: int = 1024,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ):
        """
        初始化文档存储服务
        
        Args:
            embedding_service: EmbeddingService实例
            mongo_uri: MongoDB连接URI
            mongo_db_name: MongoDB数据库名
            mongo_collection: MongoDB集合名
            qdrant_host: Qdrant主机地址
            qdrant_port: Qdrant端口
            qdrant_api_key: Qdrant API密钥
            qdrant_collection: Qdrant集合名
            embedding_dim: 向量维度（根据模型调整）
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠大小（字符数）
        """
        self.embedding_service = embedding_service
        
        # MongoDB连接
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db: Database = self.mongo_client[mongo_db_name]
        self.text_collection = self.mongo_db[mongo_collection]
        
        # Qdrant连接
        self.qdrant_client = QdrantClient(
            url=f"http://{qdrant_host}:{qdrant_port}",  # 自动拼接完整 URL
            api_key=qdrant_api_key,
            timeout=30,
            check_compatibility=False  # 跳过版本检查
        )
        
        # 存储配置
        self.qdrant_collection = qdrant_collection
        self.embedding_dim = embedding_dim
        
        # 初始化 SentenceSplitter（使用您已有的配置）
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # 确保Qdrant集合存在
        self._ensure_qdrant_collection()
    
    def _ensure_qdrant_collection(self):
        """确保Qdrant目标集合存在，不存在则创建"""
        if not self.qdrant_client.collection_exists(self.qdrant_collection):
            logger.info(f"Creating Qdrant collection: {self.qdrant_collection}")
            self.qdrant_client.create_collection(
                collection_name=self.qdrant_collection,
                vectors_config=qdrant_models.VectorParams(
                    size=self.embedding_dim,
                    distance=qdrant_models.Distance.COSINE
                )
            )
    
    def _read_document(self, file_path: str) -> str:
        """安全读取文档内容（支持多种编码）"""
        encodings = ['utf-8', 'gbk', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with codecs.open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"无法用常见编码读取文件: {file_path}")
    
    def _generate_document_id(self) -> str:
        """生成全局唯一文档ID（用于串联双库）"""
        return str(uuid.uuid4())
    
    async def _process_and_embed_nodes(self, text: str) -> List[Dict]:
        """
        使用 llama_index 的 SentenceSplitter 分块并异步生成向量
        
        Args:
            text: 原始文档文本
            
        Returns:
            包含文本、向量和元数据的节点列表
        """
        # 1. 创建 Document 对象（完全复用您的逻辑）
        document = Document(text=text)
        
        # 2. 使用 SentenceSplitter 异步获取节点
        nodes = await self.node_parser.aget_nodes_from_documents([document])
        
        # 3. 异步为每个节点生成 embedding（完全复用您的逻辑）
        for node in nodes:
            node.embedding = await self.embedding_service.aget_embedding(node.text)
        
        # 4. 转换为字典列表，方便后续处理
        node_data_list = []
        for idx, node in enumerate(nodes):
            node_data_list.append({
                "text": node.text,
                "embedding": node.embedding,
                "chunk_index": idx
            })
        
        return node_data_list
    
    async def store_document_async(self, file_path: str) -> Dict[str, Any]:
        """
        异步主流程：读取文档 -> 智能分块 -> 向量化 -> 双库存储
        
        Args:
            file_path: 本地文档路径
            
        Returns:
            存储成功的元数据 {mongo_id, qdrant_id, document_name, chunk_count}
        """
        # 1. 读取文档内容
        try:
            content = self._read_document(file_path)
            document_name = os.path.basename(file_path)
        except Exception as e:
            logger.error(f"文档读取失败 {file_path}: {str(e)}")
            raise
        
        # 2. 生成唯一ID用于串联
        doc_id = self._generate_document_id()
        
        # 3. 存储到MongoDB（先存全文）
        mongo_result = self.text_collection.insert_one({
            "_id": doc_id,
            "content": content,
            "document_name": document_name,
            "file_path": file_path,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        mongo_id = str(mongo_result.inserted_id)
        
        # 4. 使用 llama_index 分块并异步生成向量
        try:
            node_data_list = await self._process_and_embed_nodes(content)
            
            # 5. 准备Qdrant点数据
            points = []
            for node_data in node_data_list:
                point_id = str(uuid.uuid4())
                points.append(
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector=node_data['embedding'],
                        payload={
                            "mongo_id": mongo_id,
                            "document_name": document_name,
                            "chunk_index": node_data['chunk_index'],
                            "text": node_data['text'][:500]  # 存储部分文本用于调试
                        }
                    )
                )
            
            # 6. 批量上传到Qdrant
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection,
                points=points
            )
            
            logger.info(
                f"成功存储文档: {document_name} | "
                f"MongoDB ID: {mongo_id} | "
                f"Chunks: {len(node_data_list)}"
            )
            
            return {
                "mongo_id": mongo_id,
                "qdrant_id_prefix": doc_id,
                "document_name": document_name,
                "chunk_count": len(node_data_list)
            }
            
        except Exception as e:
            # 出错时清理MongoDB数据
            self.text_collection.delete_one({"_id": doc_id})
            logger.error(f"向量存储失败 {file_path}: {str(e)}")
            raise
    
    # 保留同步接口，内部自动创建事件循环
    def store_document(self, file_path: str) -> Dict[str, Any]:
        """
        同步主流程（内部自动管理事件循环）
        
        Args:
            file_path: 本地文档路径
            
        Returns:
            存储成功的元数据
        """
        try:
            loop = asyncio.get_running_loop()
            # 如果已有运行中的事件循环，创建新任务
            return loop.run_until_complete(self.store_document_async(file_path))
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self.store_document_async(file_path))

# ================= 单例服务创建 =================
# 先创建EmbeddingService实例
embedding_service = EmbeddingService(
    model=settings.embedding_model,
    api_key=settings.embedding_api_key,
    base_url=settings.embedding_base_url
)

# 再创建DocumentStorageService实例

document_storage_service = DocumentStorageService(
    embedding_service=embedding_service,
    mongo_uri=settings.mongodb_uri,  # ✅ 改为小写，与 Settings 类定义一致
    mongo_db_name=settings.mongo_db_name,
    mongo_collection=settings.mongo_text_collection,
    qdrant_host=settings.qdrant_host,  # ✅ 注意这里也是小写
    qdrant_port=settings.qdrant_port,  # ✅ 小写
    qdrant_api_key=settings.qdrant_api_key,  # ✅ 小写
    qdrant_collection=settings.qdrant_collection_name,
    embedding_dim=settings.embedding_dim
)