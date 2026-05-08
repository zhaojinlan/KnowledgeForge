# app.py
from fastapi import FastAPI
from core.config import settings
from core.cors import setup_cors
from api.v1.routes import router
from services.llm_service import LLMService
from fastapi import FastAPI
# 初始化 LLM 服务
llm_service = LLMService(
    model=settings.model,
    api_key=settings.api_key,
    base_url=settings.base_url
)

# 创建应用
app = FastAPI(title="AI Chat Service",debug=settings.debug)

# 设置 CORS
setup_cors(app)

# 注册路由
app.include_router(router)

# 根路径
@app.get("/")
def home():
    return {"message": "AI 聊天服务运行中！访问 /api/v1/chat"}


#测试配置加载是否正确
from core.config import settings
print("🔧 配置加载结果:")
print("  model    :", settings.model)
print("  api_key  :", settings.api_key[:10] + "..." if settings.api_key else "None")
print("  base_url :", settings.base_url)

print("🚀 启动 Model Server")
print("📄 App Name:", settings.app_name)
print("🔧 Debug:", settings.debug)
print("💬 LLM Model:", settings.model)
print("🔗 MongoDB URI:", settings.mongodb_uri.replace(settings.mongo_root_password, "****"))
print("🔍 Qdrant: {}:{}".format(settings.qdrant_host, settings.qdrant_port))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000,reload=True)