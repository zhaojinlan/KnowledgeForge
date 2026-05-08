# core/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
client = AsyncIOMotorClient(settings.mongodb_uri)
db = client["chat_db"]
sessions_collection = db["sessions"]
messages_collection = db["messages"]


print("✅ 正在连接 MongoDB:", settings.mongodb_uri)