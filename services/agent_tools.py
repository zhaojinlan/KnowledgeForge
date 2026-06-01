"""
Agent tools for KnowledgeForge - wrapping existing ModelServer services.
Adapted from deep-code-agent terminal.py pattern.
"""

import os
import tempfile
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _get_retrieval_tool():
    from services.embedding_service import retrieval_tool
    return retrieval_tool


def _get_minio_service():
    from services.minio_service import minio_service
    return minio_service


@tool("search_knowledge_base")
def search_knowledge_base(query: str, top_k: int = 4) -> str:
    """
    在知识库中执行混合检索（向量相似度 + 全文搜索），返回最相关的文档片段。
    当你需要查找特定信息、回答用户问题、或了解知识库中有什么内容时使用此工具。

    Args:
        query: 检索查询字符串，应使用清晰的关键词或自然语言问题
        top_k: 返回的文档片段数量，默认4
    """
    if not query or not query.strip():
        return "错误：查询字符串不能为空"

    try:
        results = _get_retrieval_tool().hybrid_search(query.strip(), top_k=top_k)
        if not results:
            return "未找到与查询相关的文档内容。知识库可能为空，或尝试使用不同的关键词。"

        parts = []
        for i, r in enumerate(results, 1):
            doc_name = r.get("document_name", "未知文档")
            text = r.get("text", "")
            score = r.get("final_score", 0)
            parts.append(
                f"--- 结果 {i} (相关度: {score:.2f}) ---\n"
                f"文档: {doc_name}\n"
                f"内容: {text}\n"
            )

        logger.info(f"search_knowledge_base: query='{query[:50]}...' -> {len(results)} results")
        return "\n".join(parts)

    except Exception as e:
        logger.error(f"search_knowledge_base failed: {e}", exc_info=True)
        return f"检索时发生错误: {str(e)}"


@tool("list_documents")
def list_documents() -> str:
    """
    列出知识库中所有已上传的文档文件及其基本信息。
    当你需要了解知识库中有哪些文档、或用户询问文档列表时使用此工具。
    """
    try:
        files = _get_minio_service().list_files()
        if not files:
            return "知识库中暂无文档。用户可以通过上传功能添加文档。"

        parts = ["知识库中的文档列表:"]
        for i, f in enumerate(files, 1):
            filename = f.get("filename", "未知")
            size_kb = (f.get("size", 0) or 0) / 1024
            last_modified = f.get("last_modified", "未知")
            parts.append(f"  {i}. {filename} ({size_kb:.1f} KB, 上传时间: {last_modified})")

        logger.info(f"list_documents: {len(files)} files found")
        return "\n".join(parts)

    except Exception as e:
        logger.error(f"list_documents failed: {e}", exc_info=True)
        return f"获取文档列表时发生错误: {str(e)}"


@tool("get_document_content")
def get_document_content(object_name: str, max_chars: int = 8000) -> str:
    """
    下载并读取知识库中文档的原始内容。
    当用户要求查看某个文档的全文内容、或需要深入分析特定文档时使用此工具。

    Args:
        object_name: MinIO 中的对象名称（文件名），可通过 list_documents 获取
        max_chars: 最大返回字符数，默认8000，超出部分将截断
    """
    if not object_name or not object_name.strip():
        return "错误：请指定要查看的文档文件名"

    object_name = object_name.strip()

    if not _get_minio_service().file_exists(object_name):
        available = [f.get("filename", "") for f in _get_minio_service().list_files()]
        hint = f"文件 '{object_name}' 不存在。当前知识库中的文件: {', '.join(available[:10])}"
        if len(available) > 10:
            hint += f" ... 等共 {len(available)} 个文件"
        return hint

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix="_" + object_name)
        os.close(fd)
        _get_minio_service().download_to_file(object_name, tmp_path)

        encodings = ["utf-8", "gbk", "latin-1", "iso-8859-1"]
        content = None
        for enc in encodings:
            try:
                with open(tmp_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return f"错误：无法解码文件 '{object_name}'，可能是二进制文件或不支持的编码"

        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... (内容已截断，共 {len(content)} 字符，显示前 {max_chars} 字符)"

        logger.info(f"get_document_content: '{object_name}' -> {len(content)} chars")
        return f"--- 文档: {object_name} ---\n{content}"

    except Exception as e:
        logger.error(f"get_document_content failed for '{object_name}': {e}", exc_info=True)
        return f"读取文档时发生错误: {str(e)}"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@tool("summarize_document")
def summarize_document(object_name: str) -> str:
    """
    检索并汇总特定文档在知识库中的关键内容片段。
    通过向量检索从指定文档中获取最重要的内容摘要。
    当用户要求总结某个文档、或需要了解文档主题时使用此工具。

    Args:
        object_name: 文档在 MinIO 中的对象名称，可通过 list_documents 获取
    """
    if not object_name or not object_name.strip():
        return "错误：请指定要总结的文档文件名"

    object_name = object_name.strip()

    if not _get_minio_service().file_exists(object_name):
        available = [f.get("filename", "") for f in _get_minio_service().list_files()]
        return f"文件 '{object_name}' 不存在。可用文件: {', '.join(available[:10])}"

    try:
        query = f"文档 {object_name} 的主要内容和关键信息"
        results = _get_retrieval_tool().hybrid_search(query, top_k=8)

        doc_results = [r for r in results if r.get("document_name") == object_name]
        if not doc_results:
            doc_results = results

        if not doc_results:
            return f"文档 '{object_name}' 存在于知识库中，但检索未返回相关片段。可能需要查看完整文档内容。"

        parts = [f"文档 '{object_name}' 的关键内容片段:"]
        for i, r in enumerate(doc_results, 1):
            text = r.get("text", "")
            score = r.get("final_score", 0)
            parts.append(f"\n片段 {i} (相关度: {score:.2f}):\n{text}")

        logger.info(f"summarize_document: '{object_name}' -> {len(doc_results)} chunks")
        return "\n".join(parts)

    except Exception as e:
        logger.error(f"summarize_document failed for '{object_name}': {e}", exc_info=True)
        return f"总结文档时发生错误: {str(e)}"


AGENT_TOOLS = [search_knowledge_base, list_documents, get_document_content, summarize_document]


def make_agent_tools() -> list:
    """Factory function returning the agent tool list (mirrors deep-code-agent pattern)."""
    return AGENT_TOOLS
