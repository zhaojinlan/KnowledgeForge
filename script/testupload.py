# 异步调用（推荐在异步框架如FastAPI中使用）
import asyncio
from services.embedding_service import document_storage_service


async def main():
    result = await document_storage_service.store_document_async("D:\ModelServer\script\铜合金在工业与先进制造中的应用与发展.md")

# 同步调用（在普通脚本中使用）
 #   result = document_storage_service.store_document("/path/to/doc.txt")

    print(f"文档 {result['document_name']} 已存储，共 {result['chunk_count']} 个块")
    
if __name__ == "__main__":
    asyncio.run(main())
