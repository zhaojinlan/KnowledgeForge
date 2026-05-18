import asyncio
from services.embedding_service import retrieval_tool

def test_rag_search():
    """
    测试 RAG 检索应用
    """
    # 1. 模拟用户提出的问题
    user_question = "铜合金的性质"
    print(f"🙋 用户提问：{user_question}\n")
    print("🔍 正在向量库中检索最相关的文本块...\n")

    # 2. 调用我们封装好的检索工具 (这里演示同步调用)
    # top_k=3 表示我们想召回最相关的 3 个文本块
    results = retrieval_tool.search(query=user_question, top_k=3)

    # 3. 打印检索结果
    if not results:
        print("⚠️ 未检索到任何相关文本块。")
        return

    print(f"✅ 成功检索到 {len(results)} 个相关文本块：\n")
    print("-" * 60)
    
    for i, res in enumerate(results):
        print(f"📄 相关片段 {i+1}:")
        print(f"   来源文档：{res.get('document_name')}")
        print(f"   块索引：{res.get('chunk_index')}")
        print(f"   文本内容：{res['text']}")
        print("-" * 60)

async def test_rag_asearch():
    """
    测试 RAG 异步检索应用
    """
    user_question = "自然语言处理是计算机科学的一部分吗？"
    print(f"🙋 用户提问：{user_question}\n")
    print("🔍 正在异步检索...\n")

    # 调用异步检索方法
    results = await retrieval_tool.asearch(query=user_question, top_k=2)
    
    print(f"✅ 异步检索成功，找到 {len(results)} 个相关文本块：\n")
    for i, res in enumerate(results):
        print(f"📄 片段 {i+1}: {res['text']}\n")

if __name__ == "__main__":
    # 运行同步检索测试
    test_rag_search()
    
    print("\n\n")
    
    # 运行异步检索测试
    asyncio.run(test_rag_asearch())