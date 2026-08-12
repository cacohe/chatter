# RAG 知识问答

基于 FastAPI + Streamlit 的**一次性本地 RAG 知识问答**：无登录、无数据库、无长期记忆。知识库从固定目录加载，对话记忆仅保存在前端本轮会话中。

## 技术栈

- **后端**: FastAPI
- **前端**: Streamlit
- **LLM**: LiteLLM 调用通义千问（`DEFAULT_LLM` 需为已登记模型）
- **检索**: 进程内分块 + 关键字重叠检索（无向量库）

## 工作方式

1. 后端启动时扫描 `data/docs`（`.txt` / `.md`），分块载入内存
2. 用户提问 → 检索相关分块 → 注入 system 上下文 → 调用默认模型流式回答
3. 前端用 `session_state` 保存本轮消息，请求时附带 `history`；「开启新对话」清空消息

## 项目结构（精简）

```
chatter/
├── data/docs/                 # 知识库文档（启动加载）
├── src/
│   ├── backend/
│   │   ├── api/routes/        # chat / knowledge
│   │   ├── app/services/      # ChatService
│   │   ├── infra/llm/         # LiteLLM 调用
│   │   └── infra/rag/         # loader / store / retriever
│   ├── frontend/              # Streamlit UI
│   └── shared/                # 配置与 schemas
├── run.py                     # 同时启动前后端
├── backend_run.py
└── frontend_run.py
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env.local`，至少配置：

```env
DASHSCOPE_API_KEY=your_key
DEFAULT_LLM=qwen3.7-max
RAG_DOCS_PATH=./data/docs
BACKEND_API_URL=http://localhost:8000/api/v1.0
```

### 3. 准备知识库

将文档放入 `data/docs/`（已有示例：请假政策等）。也可在界面上传文档，或调整分块参数后重新分块。

### 4. 启动

```bash
# 同时启动前后端
python run.py

# 或分别启动
python backend_run.py
python frontend_run.py
```

打开 Streamlit 页面即可提问。

## CI

Push / PR 到 `master` 或 `main` 时，GitHub Actions 会执行：

- **Ruff**：import 排序、语法/未使用变量检查、格式校验
- **Pytest**：`tests/unittest/test_backend`
