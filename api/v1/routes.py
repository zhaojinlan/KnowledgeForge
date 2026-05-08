# api/v1/routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from schemas.chat import ChatRequest, ChatResponse
from services.llm_service import llm_service  # 使用全局实例
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
# 聊天接口
# -------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"📨 收到聊天请求 | message='{request.message}', session_id='{request.session_id}'")

        # 如果没有 session_id，创建新会话并写入数据库
        if not request.session_id:
            session_id = str(uuid.uuid4())
            now = dt.utcnow()
            new_session = {
                "_id": session_id,
                "title": f"会话 {now.strftime('%m-%d %H:%M')}",
                "created_at": now,
                "updated_at": now
            }
            await sessions_collection.insert_one(new_session)
            logger.info(f"🆕 创建新会话 | session_id={session_id}")
        else:
            session_id = request.session_id

        # 调用 LLM 服务
        response = llm_service.chat(request.message, session_id)
        logger.info(f"🤖 LLM 返回响应 | session_id={session_id}, len={len(response)}")

        # 异步保存用户和 AI 消息
        asyncio.create_task(save_message_to_db(session_id, "user", request.message))
        asyncio.create_task(save_message_to_db(session_id, "ai", response))

        return ChatResponse(response=response, session_id=session_id)

    except Exception as e:
        logger.error(f"❌ 聊天接口异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# -------------------------------
# 文件上传接口
# -------------------------------
UPLOAD_DIR = r"D:\ModelServer\RAG"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    safe_name = file.filename.rsplit('.', 1)[0]
    folder_name = f"{timestamp}_{safe_name}"
    upload_folder = os.path.join(UPLOAD_DIR, folder_name)
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)

    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(8192):
                f.write(chunk)
    except Exception as e:
        logger.error(f"❌ 文件保存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 广播新文件上传事件
    stat = os.stat(file_path)
    new_file_info = {
        "filename": file.filename,
        "folder": folder_name,
        "size": stat.st_size,
        "path": file_path.replace("\\", "/"),
        "uploaded_at": stat.st_mtime
    }

    await manager.broadcast({
        "type": "file_uploaded",
        "data": new_file_info
    })

    logger.info(f"📁 文件上传成功 | {file_path}")
    return {
        "message": "文件上传成功",
        "filename": file.filename,
        "folder": folder_name,
        "path": file_path.replace("\\", "/")
    }


# -------------------------------
# 获取已上传文件列表
# -------------------------------
@router.get("/files")
async def list_files():
    try:
        files_info = []
        if not os.path.exists(UPLOAD_DIR):
            return files_info

        for folder_name in os.listdir(UPLOAD_DIR):
            folder_path = os.path.join(UPLOAD_DIR, folder_name)
            if not os.path.isdir(folder_path):
                continue
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files_info.append({
                        "filename": file_name,
                        "folder": folder_name,
                        "size": stat.st_size,
                        "path": file_path.replace("\\", "/"),
                        "uploaded_at": stat.st_mtime
                    })
                    break  # 每个文件夹只取一个文件展示
        files_info.sort(key=lambda x: x["uploaded_at"], reverse=True)
        logger.info(f"📋 返回 {len(files_info)} 个上传文件")
        return files_info
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
