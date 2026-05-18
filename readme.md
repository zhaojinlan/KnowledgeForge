# KnowledgeForge

AI 驱动的知识库管理与智能问答系统，基于 RAG（检索增强生成）技术，支持文档上传、自动索引、混合检索和多轮对话。

## Tech Stack

| 层 | 技术 |
|---|---|
| **前端** | Vue 3 + Vite + 原生 CSS |
| **后端** | FastAPI + Uvicorn |
| **LLM** | Qwen3-235B (GPUStack 远程推理) |
| **Embedding** | BGE-M3 (远程推理) |
| **向量库** | Qdrant |
| **文档库** | MongoDB |
| **对象存储** | MinIO |
| **文档解析** | LlamaIndex + LangChain |

## Architecture

```
┌──────────┐     HTTP      ┌───────────┐     OpenAI API     ┌──────────────┐
│  Vue 3   │ ────────────▶ │  FastAPI  │ ─────────────────▶ │  GPUStack    │
│  Frontend│ ◀──────────── │  Backend  │ ◀───────────────── │  (LLM/Embed) │
└──────────┘               └─────┬─────┘                    └──────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Qdrant  │ │ MongoDB  │ │  MinIO   │
              │ (向量检索)│ │(文档回填)│ │(文件存储) │
              └──────────┘ └──────────┘ └──────────┘
```

## Quick Start

### 1. 启动基础设施 (Docker)

```bash
docker compose up -d
```

启动后验证：
- Qdrant: `http://localhost:8333/dashboard`
- MongoDB: `mongodb://root:123456@localhost:37017`
- MinIO Console: `http://localhost:19001` (账号: minioadmin / minioadmin123)

### 2. 配置 Python 环境

```bash
conda env create -f environment.yml  # 或手动安装依赖
conda activate ms
pip install -r requirements.txt
```

### 3. 配置环境变量

复制并编辑 `.env` 文件（参考现有 `.env`）：

```env
# LLM
MODEL=Qwen3-235B-A22B-Instruct
API_KEY=your_key
BASE_URL=http://your-server:38080/v1

# Embedding
embedding_api_key=your_key
embedding_base_url=http://your-server:30110/v1/
embedding_model=bge-m3

# Database
MONGO_ROOT_USERNAME=root
MONGO_ROOT_PASSWORD=123456
MONGODB_URI=mongodb://root:123456@localhost:37017/admin

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=8333
QDRANT_API_KEY=123456

# MinIO
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
```

### 4. 启动服务

```bash
# 后端
python app.py
# 访问 http://localhost:9000/docs 查看 API 文档

# 前端
cd frontend && npm install && npm run dev
# 访问 http://localhost:5173
```

## Project Structure

```
KnowledgeForge/
├── api/v1/                  # API 路由
│   ├── routes.py            # 主路由（聊天/上传/会话/文件）
│   └── ws_manager.py        # WebSocket 连接管理
├── core/                    # 核心配置
│   ├── config.py            # Pydantic Settings (.env 读取)
│   └── database.py          # MongoDB/AsyncMongoDB 连接
├── schemas/                 # Pydantic 数据模型
│   ├── chat.py              # ChatRequest/ChatResponse
│   └── session.py           # SessionCreate/SessionOut
├── services/                # 业务服务层
│   ├── embedding_service.py # BGE 嵌入 + Qdrant 检索 + MongoDB 回填
│   ├── llm_service.py       # LLM 对话（含会话历史持久化）
│   └── minio_service.py     # MinIO 对象存储封装
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── pages/           # 页面（Chat.vue, Upload.vue, Home.vue）
│   │   └── components/      # 组件（ChatMessage.vue, Layout.vue）
│   └── vite.config.js       # Vite 配置（API 代理）
├── script/                  # 工具脚本
│   ├── llm0.py              # LLM 调试 CLI
│   ├── qdrant.py            # Qdrant 向量查看
│   └── readqdrant.py        # Qdrant 集合重建
├── docker-compose.yml       # Docker 基础设施编排
├── .env                     # 环境变量（不提交）
├── .gitignore               # Git 忽略规则
├── requirements.txt         # Python 依赖
└── app.py                   # FastAPI 应用入口
```

## API Reference

### 聊天接口
- `POST /api/v1/chat` — 发送消息，返回 AI 回复（含 RAG 上下文）
- 请求体：`{ "message": string, "session_id": string? }`

### 文件上传
- `POST /api/v1/upload` — 上传文件到 MinIO，后台自动索引
- 支持格式：PDF, DOCX, TXT, Markdown, HTML 等

### 文件列表
- `GET /api/v1/files` — 列出 MinIO 中所有上传的文件

### 会话管理
- `GET /api/v1/sessions` — 获取所有会话列表
- `POST /api/v1/sessions` — 创建新会话
- `GET /api/v1/session/{id}` — 获取会话消息历史
- `DELETE /api/v1/session/{id}` — 删除会话

### WebSocket
- `WS /api/v1/ws` — 实时通知（文档入库完成/失败）

## RAG Pipeline

1. **上传**: 文件通过 `/upload` 上传至 MinIO
2. **分块**: LlamaIndex SentenceSplitter 按句子切分（chunk_size=2048, overlap=120）
3. **向量化**: BGE-M3 模型生成 1024 维向量
4. **存储**: 向量存入 Qdrant，文本存入 MongoDB
5. **检索**: 混合检索（Qdrant 向量相似度 60% + MongoDB 全文搜索 40%）
6. **生成**: LLM 结合检索上下文生成回复

## Ports

| 服务 | 宿主机端口 | 容器端口 |
|------|-----------|---------|
| 后端 API | 9000 | 9000 |
| 前端 (Vite) | 5173 | 5173 |
| Qdrant HTTP | 8333 | 6333 |
| Qdrant gRPC | 8334 | 6334 |
| MongoDB | 37017 | 27017 |
| MinIO API | 19000 | 9000 |
| MinIO Console | 19001 | 9001 |
