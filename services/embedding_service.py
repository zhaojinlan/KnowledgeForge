# services/embedding_service.py
"""
纯 LangChain 句子分块版：
- 文档加载与切片：LangChain (RecursiveCharacterTextSplitter + 中文句子分隔符)
- 向量化与存储检索：LangChain (CustomBgeEmbeddings + Qdrant)
- 检索逻辑：Qdrant 向量召回 -> MongoDB 文本回填
"""
import codecs
from typing import List, Dict, Any
import os
import uuid
import logging
import asyncio
from datetime import datetime
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
# --- LangChain 核心组件 ---
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter # 文本拆分器
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, Docx2txtLoader, UnstructuredFileLoader,UnstructuredMarkdownLoader
)
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models  # 必须有这一行
# --- 向量库与数据库 ---
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from pymongo import MongoClient
from pymongo.database import Database
from bson.objectid import ObjectId

# --- 配置 ---
from core.config import settings

logger = logging.getLogger(__name__)


# ================== 嵌入模型服务 ==================
# 封装服务器的模型适用于langchain
class CustomBgeEmbeddings(Embeddings):
    """自定义 BGE 嵌入模型，兼容 LangChain 接口。"""
    
    def __init__(self, base_url: str = None, api_key: str = None, model: str = None, timeout: int = 30):
        self.base_url = (base_url or settings.embedding_base_url).rstrip("/") + "/embeddings"
        self.api_key = api_key or settings.embedding_api_key
        self.model = model or settings.embedding_model
        self.timeout = timeout
        
        import requests
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        logger.info(f"Embedding 服务初始化: {self.model}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.session.post(self.base_url, json={"model": self.model, "input": texts}, timeout=self.timeout)
            response.raise_for_status()
            return [item["embedding"] for item in response.json()["data"]]
        except Exception as e:
            logger.warning(f"批量嵌入失败，降级处理: {e}")
            return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        import httpx
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, json={"model": self.model, "input": texts}, headers={"Authorization": f"Bearer {self.api_key}"})
            response.raise_for_status()
            return [item["embedding"] for item in response.json()["data"]]

    async def aembed_query(self, text: str) -> List[float]:
        return (await self.aembed_documents([text]))[0]


# ================== 文档存储与切片服务 ==================
class DocumentStorageUpdService:
    def __init__(
        self,
        embedding_service: Embeddings,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        qdrant_host: str,
        qdrant_port: int,
        qdrant_api_key: str,
        qdrant_collection: str,
        embedding_dim: int = 1024,
        chunk_size: int = 512,      # 这里的值会传给 LlamaIndex
        chunk_overlap: int = 50,    # 这里的值会传给 LlamaIndex
    ):
        self.embedding_service = embedding_service
        
        # --- MongoDB 初始化 ---
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db: Database = self.mongo_client[mongo_db_name]
        self.text_collection = self.mongo_db[mongo_collection]
        
        # --- Qdrant 初始化 ---
        self.qdrant_client = QdrantClient(
            url=f"http://{qdrant_host}:{qdrant_port}", 
            api_key=qdrant_api_key, 
            timeout=30
        )
        self.qdrant_collection = qdrant_collection
        self.embedding_dim = embedding_dim
        
        # --- 【关键修改】初始化 LlamaIndex SentenceSplitter ---
        # 注意：LlamaIndex 的 SentenceSplitter 默认按 token 算，但设置 chunk_size 后也能按字符切
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # 如果你的文本是纯中文且想严格按字符数切，可以设置 tokenizer 为 len
            # tokenizer=lambda x: list(x), 
        )
        
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
    # ... (ensure_qdrant_collection, _get_loader, _read_document 方法保持不变) ...

    def store_document(self, file_path: str) -> Dict[str, Any]:
        """
        同步调用入口，用于在非异步环境中直接调用。
        """
        try:
            # 尝试获取当前正在运行的事件循环
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.store_document_async(file_path))
        except RuntimeError:
            # 如果没有正在运行的循环，则创建一个新的并运行
            return asyncio.run(self.store_document_async(file_path))

    async def store_document_async(self, file_path: str) -> Dict[str, Any]:
        document_name = os.path.basename(file_path)
        
        # 1. 读取文档内容
        content = self._read_document(file_path)
        if not content.strip():
            raise ValueError("文档内容为空")

        # 2. 【核心逻辑】使用 LlamaIndex 进行切片
        # 将读取的文本包装成 LlamaIndex 的 Document 对象
        llama_doc = LlamaDocument(text=content)
        
        # 异步切片
        nodes = await self.node_parser.aget_nodes_from_documents([llama_doc])
        
        if not nodes:
            raise ValueError("文档切片后为空")

        # 3. 存入 MongoDB (将切片文本存为列表)
        doc_id = str(uuid.uuid4())
        chunks = [node.text for node in nodes]
        
        mongo_result = self.text_collection.insert_one({
            "_id": doc_id,
            "document_name": document_name,
            "chunks": chunks,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        mongo_id = str(mongo_result.inserted_id)

        # 4. 【核心逻辑】异步向量化
        # 使用你现有的 embedding_service 进行异步调用
        embeddings = []
        for node in nodes:
            # 修改前：embedding = await self.embedding_service.aget_embedding(node.text)
            # 修改后：使用标准的 aembed_query 方法
            embedding = await self.embedding_service.aembed_query(node.text)
            embeddings.append(embedding)


        # 5. 存入 Qdrant
        points = []
        for idx, (node, embedding) in enumerate(zip(nodes, embeddings)):
            points.append(qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "mongo_id": mongo_id,
                    "document_name": document_name,
                    "chunk_index": idx,
                    "text": node.text[:100]  # 可选：存一点文本预览方便调试
                }
            ))
        
        self.qdrant_client.upsert(collection_name=self.qdrant_collection, points=points)
        
        print(f" 成功存储: {document_name} | 切片数: {len(chunks)}")
        return {
            "mongo_id": mongo_id, 
            "document_name": document_name, 
            "chunk_count": len(chunks)
        }
# ================== 检索工具类 (向量召回 + MongoDB 文本回填) ==================
class LangChainRetrievalTool:
    """
    基于 LangChain 封装的检索工具。
    流程：Qdrant 向量召回 -> 拿到 mongo_id 和 chunk_index -> 去 MongoDB 捞取完整文本块。
    """
    def __init__(
        self,
        embedding_service: Embeddings,
        mongo_uri: str,
        mongo_db_name: str,
        mongo_collection: str,
        qdrant_host: str,
        qdrant_port: int,
        qdrant_api_key: str,
        qdrant_collection: str,
    ):
        self.embedding_service = embedding_service
        
        # MongoDB 连接 (用于回填文本)
        mongo_client = MongoClient(mongo_uri)
        self.text_collection = mongo_client[mongo_db_name][mongo_collection]
        
        # LangChain Qdrant 向量库 (用于向量检索)
        qdrant_client = QdrantClient(url=f"http://{qdrant_host}:{qdrant_port}", api_key=qdrant_api_key)
        self.vectorstore = Qdrant(client=qdrant_client, collection_name=qdrant_collection, embeddings=embedding_service)

        try:
            self.text_collection.create_index([("chunks", "text")])
            logger.info("MongoDB text index ensured on 'chunks' field")
        except Exception as e:
            logger.warning(f"Could not create text index (may already exist): {e}")

    def _resolve_chunk_text(self, mongo_id: str, chunk_index: int) -> tuple[str, str]:
        """从 MongoDB 获取指定 chunk 的完整文本和文档名。"""
        doc_data = self.text_collection.find_one({"_id": mongo_id}, {"chunks": 1, "document_name": 1})
        if doc_data and "chunks" in doc_data:
            all_chunks = doc_data["chunks"]
            doc_name = doc_data.get("document_name", "Unknown")
            if 0 <= chunk_index < len(all_chunks):
                return all_chunks[chunk_index], doc_name
        return "", "Unknown"

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """执行语义检索，返回来自 MongoDB 的完整文本块。"""
        # 1. 在 Qdrant 中进行向量相似度检索
        docs = self.vectorstore.similarity_search(query, k=top_k)
        
        # 2. 提取需要去 MongoDB 查询的 ID 和对应的索引
        mongo_queries = {}
        for doc in docs:
            payload = doc.metadata
            mongo_id = payload.get("mongo_id")
            chunk_index = payload.get("chunk_index")
            if mongo_id and chunk_index is not None:
                mongo_queries.setdefault(mongo_id, []).append(chunk_index)

        # 3. 批量去 MongoDB 捞取完整的文本块
        final_results = []
        for mongo_id, indices in mongo_queries.items():
            doc_data = self.text_collection.find_one({"_id": mongo_id}, {"chunks": 1, "document_name": 1})
            if doc_data and "chunks" in doc_data:
                all_chunks = doc_data["chunks"]
                doc_name = doc_data.get("document_name", "Unknown")
                for idx in indices:
                    if 0 <= idx < len(all_chunks):
                        final_results.append({
                            "text": all_chunks[idx],  
                            "document_name": doc_name,
                            "chunk_index": idx,
                            "mongo_id": mongo_id
                        })
        return final_results

    async def asearch(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """异步检索"""
        docs = await self.vectorstore.asimilarity_search(query, k=top_k)
        mongo_queries = {}
        for doc in docs:
            payload = doc.metadata
            mongo_id = payload.get("mongo_id")
            chunk_index = payload.get("chunk_index")
            if mongo_id and chunk_index is not None:
                mongo_queries.setdefault(mongo_id, []).append(chunk_index)

        final_results = []
        for mongo_id, indices in mongo_queries.items():
            doc_data = self.text_collection.find_one({"_id": mongo_id}, {"chunks": 1, "document_name": 1})
            if doc_data and "chunks" in doc_data:
                for idx in indices:
                    if 0 <= idx < len(doc_data["chunks"]):
                        final_results.append({"text": doc_data["chunks"][idx], "document_name": doc_data.get("document_name"), "chunk_index": idx})
        return final_results

    def hybrid_search(self, query: str, top_k: int = 4, vector_weight: float = 0.6) -> List[Dict[str, Any]]:
        """
        混合检索：向量相似度 (Qdrant) + MongoDB 全文搜索。
        结果按文本内容去重，加权评分后排序取 top_k。
        """
        results: Dict[str, Dict] = {}

        # --- 向量搜索分支 ---
        vector_docs = self.vectorstore.similarity_search(query, k=top_k)
        for doc in vector_docs:
            payload = doc.metadata
            mongo_id = payload.get("mongo_id")
            chunk_index = payload.get("chunk_index")
            if mongo_id and chunk_index is not None:
                text, doc_name = self._resolve_chunk_text(mongo_id, chunk_index)
                if text and text not in results:
                    results[text] = {
                        "text": text,
                        "document_name": doc_name,
                        "vector_score": 1.0,
                        "mongo_score": 0.0,
                        "sources": ["vector"],
                        "chunk_index": chunk_index,
                        "mongo_id": mongo_id,
                    }

        # --- MongoDB 全文搜索分支 ---
        try:
            mongo_docs = self.text_collection.find(
                {"$text": {"$search": query}},
                {"chunks": 1, "document_name": 1, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)

            for doc in mongo_docs:
                doc_name = doc.get("document_name", "Unknown")
                mongo_score = doc.get("score", 0)
                normalized_score = min(mongo_score / 5.0, 1.0) if mongo_score else 0.0
                mongo_id = str(doc["_id"])

                if "chunks" in doc:
                    for idx, chunk_text in enumerate(doc["chunks"][:2]):
                        if chunk_text and chunk_text not in results:
                            results[chunk_text] = {
                                "text": chunk_text,
                                "document_name": doc_name,
                                "vector_score": 0.0,
                                "mongo_score": normalized_score,
                                "sources": ["mongodb_fts"],
                                "chunk_index": idx,
                                "mongo_id": mongo_id,
                            }
        except Exception as e:
            logger.warning(f"MongoDB full-text search failed: {e}")

        # --- 合并与排序 ---
        ranked = []
        for data in results.values():
            score = data["vector_score"] * vector_weight + data["mongo_score"] * (1 - vector_weight)
            data["final_score"] = round(score, 4)
            ranked.append(data)

        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked[:top_k]


# ================== 全局实例化 ==================
embedding_service = CustomBgeEmbeddings()

# 存储服务
document_storage_service = DocumentStorageUpdService(
    embedding_service=embedding_service,
    mongo_uri=settings.mongodb_uri,
    mongo_db_name=settings.mongo_db_name,
    mongo_collection=settings.mongo_text_collection,
    qdrant_host=settings.qdrant_host,
    qdrant_port=settings.qdrant_port,
    qdrant_api_key=settings.qdrant_api_key,
    qdrant_collection=settings.qdrant_collection_name,
    embedding_dim=settings.embedding_dim,
    chunk_size=2048,      # 句子分块的范围
    chunk_overlap=120,    # 块之间的重叠
)

# 检索工具
retrieval_tool = LangChainRetrievalTool(
    embedding_service=embedding_service,
    mongo_uri=settings.mongodb_uri,
    mongo_db_name=settings.mongo_db_name,
    mongo_collection=settings.mongo_text_collection,
    qdrant_host=settings.qdrant_host,
    qdrant_port=settings.qdrant_port,
    qdrant_api_key=settings.qdrant_api_key,
    qdrant_collection=settings.qdrant_collection_name,
)