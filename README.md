# RAG 知识问答

基于 FastAPI + Streamlit 的 **RAG 知识问答系统**：无需登录、无长期记忆。知识可来自 PDF / Markdown / TXT、数据库只读查询或网页；对话展示历史仅在内存中，无持久化。

## 技术栈

- **后端**: FastAPI（`backend/`）
- **前端**: Streamlit（`frontend/`）
- **LLM**: LiteLLM 流式调用（如 DashScope）
- **检索**: LlamaIndex 句子分块 + Qdrant 向量检索；

## 项目结构

```
chatter/
├── backend/                   # FastAPI 独立部署
│   ├── src/                   # api / app / domain / infra；入口 main.py
│   ├── tests/
│   └── pyproject.toml
└── frontend/                  # Streamlit 独立部署
    ├── src/main.py            # Streamlit 入口
    ├── tests/
    └── pyproject.toml
```

## 自定义设计

分块、向量化和检索使用 LlamaIndex + Qdrant。为补齐产品与安全缺口自行实现：

- **引用校验**：检索块统一编成 `[n]` 写入 prompt；生成后再核对正文里实际出现的编号，前端区分已引用 / 检索到但未引用，避免把未使用的来源当成证据。
- **来源身份与覆盖导入**：文件用文件名，网页用规范化 URL，数据库用脱敏连接串 + SQL，生成稳定 `source_id`；同一来源再导入会替换旧分块，而不是堆出多份。`source_uri` 只用于展示和核验（网页可回点、数据库连接串脱敏）。
- **导入边界**：限制上传数量与体积；网页自行抓取（补 UA、修中文编码），只允许公网 `http/https`，拒绝本机/私网且不跟随跳转，并过滤「请开启 JavaScript」一类壳页面；数据库只执行单条 `SELECT`，并限制行数与单行长度。

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

后端至少配置 `DASHSCOPE_API_KEY`、`DEFAULT_LLM`，以及 Qdrant 的 `QDRANT_MODE=cloud`、`QDRANT_URL`、`QDRANT_API_KEY`。前端配置 `BACKEND_API_URL`。

### 3. 启动

```bash
# 后端（在 backend/ 目录）
PYTHONPATH=src uv run python -m main

# 前端（在 frontend/ 目录）
PYTHONPATH=src uv run streamlit run src/main.py
```

## Render 部署

### 后端

```bash
cd backend
uv sync
PYTHONPATH=src uv run python -m main
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
