# services/embedding_service.py
from typing import List, Any
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from core.config import settings
import os
import asyncio


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
            show_progress=False,  # 可根据需要开启
        )
        return result  # List[List[float]]

# ✅ 创建并导出单例服务 
embedding_service = EmbeddingService( model=settings.embedding_model, api_key=settings.embedding_api_key, base_url=settings.embedding_base_url) 