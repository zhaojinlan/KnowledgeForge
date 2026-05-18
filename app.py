# app.py
from fastapi import FastAPI
from core.config import settings
from core.cors import setup_cors
from api.v1.routes import router

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


# Test config loading
from core.config import settings
print("Config loaded:")
print("  model    :", settings.model)
print("  api_key  :", settings.api_key[:10] + "..." if settings.api_key else "None")
print("  base_url :", settings.base_url)

print("Starting Model Server")
print("  App Name:", settings.app_name)
print("  Debug:", settings.debug)
print("  LLM Model:", settings.model)
print("  MongoDB URI:", settings.mongodb_uri.replace(settings.mongo_root_password, "****"))
print("  Qdrant: {}:{}".format(settings.qdrant_host, settings.qdrant_port))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)