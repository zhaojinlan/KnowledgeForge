# script/testupload.py

from services.embedding_service import document_storage_service 

if __name__ == "__main__":
    # 实例化服务 (注意：这里的参数会传递给 LlamaIndex 的 SentenceSplitter)
    service =document_storage_service

    file_path = r"D:\ModelServer\script\铜合金在工业与先进制造中的应用与发展.md"

    try:
        result = service.store_document(file_path)
        print("结果:", result)
    except Exception as e:
        print("错误:", str(e))