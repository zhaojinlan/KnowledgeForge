qdrant配置：
qdrant_client = QdrantClient(
            url=f"http://{qdrant_host}:{qdrant_port}",  # 自动拼接完整 URL
            api_key=qdrant_api_key,
            timeout=30,
            check_compatibility=False  # 跳过版本检查
        )

