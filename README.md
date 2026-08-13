# RAG 知识问答

基于 FastAPI + Streamlit 的**一次性本地 RAG 知识问答**：无登录、无数据库、无长期记忆。知识库从固定目录加载，对话记忆仅保存在前端本轮会话中。

## 技术栈

- **后端**: FastAPI（`backend/`）
- **前端**: Streamlit（`frontend/`）
- **LLM**: LiteLLM 调用通义千问（`DEFAULT_LLM` 需为已登记模型）
- **检索**: 进程内分块 + 关键字重叠检索（无向量库）

## 工作方式

1. 后端启动时扫描 `backend/data/docs`（`.txt` / `.md`），分块载入内存
2. 用户提问 → 检索相关分块 → 注入 system 上下文 → 调用默认模型流式回答
3. 前端用 `session_state` 保存本轮消息，请求时附带 `history`；「开启新对话」清空消息

## 项目结构

```
chatter/
├── backend/                   # FastAPI 独立部署
│   ├── src/                   # api / app / domain / infra；入口 main.py
│   ├── data/docs/
│   ├── tests/
│   └── pyproject.toml
└── frontend/                  # Streamlit 独立部署
    ├── pyproject.toml
    ├── requirements.txt
    └── src/main.py            # Cloud / Streamlit 入口
```

## 快速开始（本地）

### 1. 安装依赖

```bash
cd backend && uv sync --all-groups
cd ../frontend && uv sync
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
cd backend && PYTHONPATH=src uv run python -m main

# 前端
cd frontend && PYTHONPATH=src uv run streamlit run src/main.py
```

## 分开部署

### 后端

```bash
cd backend
uv sync
PYTHONPATH=src uv run python -m main
```

环境变量见 `backend/.env.example`。生产保持 `RELOAD=false`；云平台 `PORT` 优先生效。探活：`GET /health`。

### 前端（Streamlit Cloud）

- 入口：`frontend/src/main.py`
- 依赖：`frontend/requirements.txt`（由 `uv export --no-dev -o requirements.txt` 生成）
- Secrets：

```toml
BACKEND_API_URL = "https://你的后端域名/api/v1.0"
```

## CI

Push / PR 到 `master` 或 `main` 时，对 `backend/` 执行 Ruff + Pytest。
