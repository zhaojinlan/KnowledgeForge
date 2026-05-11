# script/testrag.py
from services.embedding_service import embedding_service

if __name__ == "__main__":
    text = "这是一个测试句子。"
    emb = embedding_service.get_embedding(text)
    print(f"Embedding length: {len(emb)}")
    print(f"First 5 dims: {emb[:5]}")
