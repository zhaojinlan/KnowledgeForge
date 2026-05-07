# api/v1/routes.py
from fastapi import APIRouter, HTTPException
from schemas.chat import ChatRequest, ChatResponse

# 确保你已经在 services/llm_service.py 中创建了实例
from services.llm_service import llm_service  # ← 是实例，不是类！

router = APIRouter(prefix="/api/v1")

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        print("🎯 接收到请求:")
        print("  message:", request.message)
        print("  history:", request.history)

        # ✅ 正确：调用实例方法
        response = llm_service.chat(request.message, request.history)

        return ChatResponse(response=response)

    except Exception as e:
        print("❌ 模型调用失败！详细错误：")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"模型调用失败: {str(e)}")