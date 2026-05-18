# api/v1/routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from schemas.chat import ChatRequest, ChatResponse
from services.llm_service import llm_service  # 使用全局实例
from services.embedding_service import retrieval_tool, document_storage_service
from services.minio_service import minio_service
from .ws_manager import manager
import os
import datetime
from datetime import datetime as dt
from core.database import sessions_collection, messages_collection
from schemas.session import SessionOut, SessionCreate
from bson import ObjectId
import uuid
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# 打印模型字段用于调试
print("🎯 ChatRequest 字段:", ChatRequest.model_json_schema()["properties"])


# -------------------------------
# 辅助函数：保存消息到数据库
# -------------------------------
async def save_message_to_db(session_id: str, role: str, content: str):
    try:
        now = dt.utcnow()
        # 确保会话存在（更新时间 or 创建）
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {"updated_at": now},
                "$setOnInsert": {"title": "未命名会话", "created_at": now}
            },
            upsert=True
        )
        # 保存消息
        result = await messages_collection.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": now
        })
        logger.info(f"✅ 消息已保存 | session_id={session_id}, role={role}, id={result.inserted_id}")
    except Exception as e:
        logger.error(f"❌ 保存消息失败 | session_id={session_id}, role={role}, error={str(e)}")


# -------------------------------
# 辅助函数：后台文档入库（MinIO 来源）
# -------------------------------
async def ingest_file_from_minio(object_name: str, temp_path: str):
    """后台任务：从 MinIO 下载文件，进行文档索引处理，然后清理临时文件。"""
    try:
        logger.info(f"🔄 开始从 MinIO 处理文档: {object_name}")
        minio_service.download_to_file(object_name, temp_path)
        result = await document_storage_service.store_document_async(temp_path)
        logger.info(f"✅ MinIO 文档入库完成: {result}")
        # 广播
        await manager.broadcast({
            "type": "ingestion_complete",
            "data": {
                "filename": object_name,
                "chunks": result.get("chunk_count", 0)
            }
        })
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        logger.error(f"❌ MinIO 文档入库失败: {object_name} | {e}", exc_info=True)
        await manager.broadcast({
            "type": "ingestion_failed",
            "data": {"filename": object_name, "error": str(e)}
        })
    finally:
        # 确保临时文件被清理
        if os.path.exists(temp_path):
            os.remove(temp_path)


# -------------------------------
# 辅助函数：后台文档入库（本地来源，保留兼容）
# -------------------------------
async def ingest_file_async(file_path: str):
    """后台异步任务：将上传的文件分块、向量化并存入 RAG 数据库。"""
    try:
        logger.info(f"🔄 开始文档入库: {file_path}")
        result = await document_storage_service.store_document_async(file_path)
        logger.info(f"✅ 文档入库完成: {result}")
        await manager.broadcast({
            "type": "ingestion_complete",
            "data": {
                "filename": os.path.basename(file_path),
                "chunks": result.get("chunk_count", 0)
            }
        })
    except Exception as e:
        logger.error(f"❌ 文档入库失败: {file_path} | {e}", exc_info=True)
        await manager.broadcast({
            "type": "ingestion_failed",
            "data": {"filename": os.path.basename(file_path), "error": str(e)}
        })


# -------------------------------
# 聊天接口
# -------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"📨 收到聊天请求 | message='{request.message}', session_id='{request.session_id}'")

        # 如果没有 session_id，创建新会话
        if not request.session_id:
            session_id = str(uuid.uuid4())
            now = dt.utcnow()
            title = request.message[:20].strip()
            if len(request.message) > 20:
                title += "..."
            new_session = {
                "_id": session_id,
                "title": title,
                "created_at": now,
                "updated_at": now
            }
            await sessions_collection.insert_one(new_session)
            logger.info(f"🆕 创建新会话 | session_id={session_id}, title='{title}'")
        else:
            session_id = request.session_id

        # 统一检查：如果会话标题是通用标题，替换为用户第一条消息摘要
        try:
            session_doc = await sessions_collection.find_one({"_id": session_id})
            if session_doc:
                current_title = session_doc.get("title", "")
                generic_titles = ["未命名会话", "新会话", "AI 聊天助手", "会话"]
                logger.info(f"🔍 标题检查 | session_id={session_id}, title='{current_title}'")
                if any(current_title == t or current_title.startswith(t) for t in generic_titles):
                    # 确认这是该会话的第一条消息
                    msg_count = await messages_collection.count_documents({"session_id": session_id})
                    logger.info(f"🔍 消息计数 | session_id={session_id}, count={msg_count}")
                    if msg_count == 0:
                        new_title = request.message[:20].strip()
                        if len(request.message) > 20:
                            new_title += "..."
                        await sessions_collection.update_one(
                            {"_id": session_id},
                            {"$set": {"title": new_title}}
                        )
                        logger.info(f"📝 自动更新会话标题 | session_id={session_id}, old='{current_title}', new='{new_title}'")
                    else:
                        logger.info(f"🔍 非首次消息，跳过标题更新")
                else:
                    logger.info(f"🔍 标题非通用，跳过更新")
        except Exception as e:
            logger.error(f"自动标题更新异常: {e}", exc_info=True)

        # 调用 LLM 服务（带 RAG 上下文）
        rag_context = ""
        try:
            retrieval_results = await asyncio.to_thread(retrieval_tool.hybrid_search, request.message, top_k=4)
            if retrieval_results:
                rag_context = "\n\n---\n\n".join(
                    f"[文档: {r['document_name']}]\n{r['text']}" for r in retrieval_results
                )
                logger.info(f"📚 RAG 检索到 {len(retrieval_results)} 条相关文档片段")
        except Exception as e:
            logger.warning(f"RAG 检索失败，将不使用上下文: {e}")

        response = llm_service.chat_with_context(request.message, session_id, rag_context)
        logger.info(f"🤖 LLM 返回响应 | session_id={session_id}, len={len(response)}")

        # 异步保存用户和 AI 消息
        asyncio.create_task(save_message_to_db(session_id, "user", request.message))
        asyncio.create_task(save_message_to_db(session_id, "ai", response))

        return ChatResponse(response=response, session_id=session_id)

    except Exception as e:
        logger.error(f"❌ 聊天接口异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# -------------------------------
# 文件上传接口 (MinIO)
# -------------------------------
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tmp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    # 保存到临时文件
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    temp_path = os.path.join(TEMP_DIR, safe_name)

    with open(temp_path, "wb") as f:
        while chunk := await file.read(8192):
            f.write(chunk)

    # 上传到 MinIO
    object_name = minio_service.upload_file(temp_path, safe_name)
    logger.info(f"📁 文件上传到 MinIO | {object_name}")

    # 清理上传临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 后台异步触发文档入库（从 MinIO 下载到单独临时路径处理，由 ingest 任务负责清理）
    ingest_temp_path = os.path.join(TEMP_DIR, f"ingest_{safe_name}")
    asyncio.create_task(ingest_file_from_minio(object_name, ingest_temp_path))

    return {
        "message": "文件上传成功，正在后台处理文档索引",
        "filename": file.filename,
        "object_name": object_name,
    }


# -------------------------------
# 获取已上传文件列表 (MinIO)
# -------------------------------
@router.get("/files")
async def list_files():
    try:
        files = minio_service.list_files()
        logger.info(f"📋 返回 {len(files)} 个上传文件")
        return files
    except Exception as e:
        logger.error(f"❌ 读取文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"读取文件列表失败: {str(e)}")


# -------------------------------
# WebSocket 实时通知
# -------------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 可处理客户端消息（如心跳、认证）
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("🔗 WebSocket 客户端断开连接")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"❌ WebSocket 错误: {e}")


# -------------------------------
# 会话管理接口
# -------------------------------

@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions():
    cursor = sessions_collection.find().sort("updated_at", -1)
    sessions = []
    async for session in cursor:
        session["id"] = str(session.pop("_id"))
        sessions.append(SessionOut(**session))
    logger.info(f"📋 返回 {len(sessions)} 个会话")
    return sessions


@router.post("/sessions", response_model=SessionOut)
async def create_session(data: SessionCreate):
    now = dt.utcnow()
    title = data.title or f"新会话 {now.strftime('%H:%M')}"
    session_id = str(uuid.uuid4())

    session = {
        "_id": session_id,
        "title": title,
        "created_at": now,
        "updated_at": now
    }
    await sessions_collection.insert_one(session)
    logger.info(f"🆕 API 创建新会话 | session_id={session_id}, title='{title}'")

    session["id"] = str(session.pop("_id"))
    return SessionOut(**session)


@router.get("/session/{session_id}")
async def get_session_history(session_id: str):
    logger.info(f"🔍 查询会话历史 | session_id={session_id}")

    # 检查会话是否存在
    session = await sessions_collection.find_one({"_id": session_id})
    if not session:
        logger.warning(f"❌ 会话不存在 | session_id={session_id}")
        raise HTTPException(status_code=404, detail="会话不存在")

    # 查询消息
    cursor = messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
    messages = []
    async for msg in cursor:
        messages.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "content": msg["content"]
        })

    logger.info(f"📨 返回会话数据 | session_id={session_id}, messages={len(messages)}")

    return {
        "session": {
            "id": session_id,
            "title": session["title"]
        },
        "messages": messages
    }

# -------------------------------
# 删除指定会话
# -------------------------------
@router.delete("/session/{session_id}", response_model=dict)
async def delete_session(session_id: str):
    try:
        logger.info(f"🗑️ 尝试删除会话 | session_id={session_id}")

        # 检查会话是否存在
        session = await sessions_collection.find_one({"_id": session_id})
        if not session:
            logger.warning(f"❌ 会话不存在，无法删除 | session_id={session_id}")
            raise HTTPException(status_code=404, detail="会话不存在")

        # 删除该会话的所有消息
        delete_result = await messages_collection.delete_many({"session_id": session_id})
        logger.info(f"🗑️ 已删除 {delete_result.deleted_count} 条相关消息 | session_id={session_id}")

        # 删除会话本身
        delete_session_result = await sessions_collection.delete_one({"_id": session_id})
        if delete_session_result.deleted_count == 0:
            logger.error(f"❌ 删除会话文档失败 | session_id={session_id}")
            raise HTTPException(status_code=500, detail="删除会话失败")

        logger.info(f"✅ 成功删除会话 | session_id={session_id}")
        return {"message": "会话删除成功", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除会话时发生异常 | session_id={session_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")
