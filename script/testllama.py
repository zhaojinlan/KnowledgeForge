from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
import asyncio
from services.embedding_service import embedding_service
# 示例文本
text = """
这里是输入
"""

# 1. 创建 Document 对象
document = Document(text=text)

# 2. 初始化 SentenceSplitter
node_parser = SentenceSplitter(
    chunk_size=500,
    chunk_overlap=100,
)

# 3. 定义异步主函数
async def main():
    nodes = await node_parser.aget_nodes_from_documents([document])
    for node in nodes:
        node.embedding =await embedding_service.aget_embedding(node.text)

    
    # 4. 打印结果
    for idx, node in enumerate(nodes):
        print(f"--- Chunk {idx + 1} ---")
        print(node.text.strip())
        print(f"First 5 dims: {node.embedding[:5]}")
        print()



# 5. 运行异步函数
if __name__ == "__main__":
    asyncio.run(main())
