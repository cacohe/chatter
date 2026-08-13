# RAG 知识问答

基于 FastAPI + Streamlit 的**一次性本地 RAG 知识问答**：无需登录、无长期记忆。知识可来自 PDF / Markdown 文件、数据库同步或网页；对话记忆仅保存在前端本轮会话中。

## 技术栈

- **后端**: FastAPI（`backend/`）
- **前端**: Streamlit（`frontend/`）
- **LLM**: LiteLLM 调用 LLM
- **检索**: LlamaIndex 加载 / 句子分块 + BM25 检索（无向量库）

## 项目结构

```
chatter/
├── backend/                   # FastAPI 独立部署
│   ├── src/                   # api / app / domain / infra；入口 main.py
│   ├── data/docs/
│   ├── tests/
│   └── pyproject.toml
└── frontend/                  # Streamlit 独立部署
    ├── src/main.py            # Streamlit 入口
    ├── tests/
    └── pyproject.toml
```

## 快速开始（本地）

### 1. 安装依赖

```bash
cd backend && uv sync --all-groups
cd ../frontend && uv sync --all-groups
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

后端至少配置 `DASHSCOPE_API_KEY`、`DEFAULT_LLM`；前端配置 `BACKEND_API_URL`。

### 3. 启动

```bash
# 后端
cd backend &&  uv run python -m main

# 前端
cd frontend &&  uv run streamlit run src/main.py
```

## Render 部署

### 后端

```bash
cd backend
uv sync
uv run python -m main
```

环境变量见 `backend/.env.example`。生产保持 `RELOAD=false`；云平台 `PORT` 优先生效。探活：`GET /health`。

### 前端

```bash
cd frontend
uv sync
PYTHONPATH=src uv run streamlit run src/main.py
```

环境变量见 `frontend/.env.example`。

## CI

Push / PR 到 `master` 或 `main` 时，分别对 `backend/`、`frontend/` 执行 Ruff + Pytest。
