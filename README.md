# Caco AI Chat

基于 FastAPI 后端 + Streamlit 前端的 AI 聊天应用，支持多种 LLM 提供商。

## 技术栈

- **后端**: FastAPI
- **前端**: Streamlit
- **数据库**: PostgreSQL + SQLAlchemy + Supabase
- **LLM 支持**: OpenAI, Qwen (Dashscope), Gemini, DeepSeek

## 项目结构

```
chatter/
├── src/
│   ├── backend/                    # FastAPI 后端
│   │   ├── api/                    # API 层
│   │   │   ├── deps.py             # 依赖注入
│   │   │   └── routes/             # 路由
│   │   │       ├── auth.py         # 认证路由
│   │   │       ├── chat.py         # 聊天路由
│   │   │       ├── llm.py          # LLM 路由
│   │   │       └── session.py      # 会话路由
│   │   ├── app/                    # 应用服务层
│   │   │   └── services/
│   │   │       ├── auth.py         # 认证服务
│   │   │       ├── chat.py         # 聊天服务
│   │   │       ├── llm.py          # LLM 服务
│   │   │       └── session.py      # 会话服务
│   │   ├── domain/                 # 领域层
│   │   │   ├── entities/           # 实体
│   │   │   │   ├── message.py
│   │   │   │   ├── session.py
│   │   │   │   └── user.py
│   │   │   ├── exceptions.py       # 异常定义
│   │   │   ├── lifecycle/           # 生命周期事件
│   │   │   ├── middleware/         # 中间件
│   │   │   │   └── error_handler.py
│   │   │   └── repository_interfaces/  # 仓储接口
│   │   │       ├── auth.py
│   │   │       ├── chat.py
│   │   │       ├── llm.py
│   │   │       └── session.py
│   │   ├── infra/                  # 基础设施层
│   │   │   ├── db/
│   │   │   │   ├── pg/             # PostgreSQL
│   │   │   │   │   └── models.py
│   │   │   │   └── supabase/       # Supabase 客户端
│   │   │   │       └── client.py
│   │   │   ├── llm/                # LLM 适配器
│   │   │   │   ├── base.py
│   │   │   │   ├── factory.py
│   │   │   │   ├── registry.py
│   │   │   │   ├── schema.py
│   │   │   │   └── providers/
│   │   │   │       ├── openai_adapter.py
│   │   │   │       ├── qwen_adapter.py
│   │   │   │       └── gemini_adapter.py
│   │   │   └── repositories/       # 仓储实现
│   │   │       ├── sqlalchemy/
│   │   │       └── supabase/
│   │   └── main.py                  # 后端入口
│   │
│   ├── frontend/                   # Streamlit 前端
│   │   ├── components/             # UI 组件
│   │   │   ├── chat.py
│   │   │   ├── header.py
│   │   │   ├── utils.py
│   │   │   └── sidebar/
│   │   │       ├── auth.py
│   │   │       ├── sidebar.py
│   │   │       └── user.py
│   │   ├── services/               # API 客户端
│   │   │   ├── api_client.py
│   │   │   ├── session.py
│   │   │   └── user.py
│   │   ├── states/                 # 状态管理
│   │   │   ├── session.py
│   │   │   └── user.py
│   │   ├── logic/                  # 业务逻辑
│   │   │   ├── config.py
│   │   │   ├── session.py
│   │   │   └── user.py
│   │   ├── utils/                  # 工具函数
│   │   │   └── validator.py
│   │   └── main.py                 # 前端入口
│   │
│   └── shared/                      # 共享模块
│       ├── config.py                # 配置管理
│       ├── logger.py                # 日志
│       ├── utils.py                 # 工具函数
│       └── schemas/                 # Pydantic schemas
│           ├── auth.py
│           ├── chat.py
│           ├── llm.py
│           └── session.py
│
├── tests/                           # 测试代码
│   └── unittest/                    # 单元测试
│
├── backend_run.py                   # 后端启动脚本
├── frontend_run.py                   # 前端启动脚本
├── requirements.txt                 # 依赖说明
├── requirements-backend.txt         # 后端依赖
├── requirements-frontend.txt        # 前端依赖
├── requirements-test.txt            # 测试依赖
└── pytest.ini                       # pytest 配置
```

## 功能特性

- 用户认证 (JWT)
- 聊天会话管理
- 多 LLM 模型支持 (OpenAI GPT, Qwen, Gemini, DeepSeek)
- 流式响应
- 历史消息分页查询

## 快速开始

### 1. 安装依赖

```bash
# 安装后端依赖
pip install -r requirements-backend.txt

# 安装前端依赖
pip install -r requirements-frontend.txt

# 安装测试依赖
pip install -r requirements-test.txt

# 或安装全部
pip install -r requirements-backend.txt -r requirements-frontend.txt -r requirements-test.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
# LLM 配置
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DEFAULT_LLM=qwen3.5-plus

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/chatter
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# JWT 配置
JWT_SECRET_KEY=your-secret-key

# 后端配置
BACKEND_LISTEN_ADDR=0.0.0.0
BACKEND_LISTEN_PORT=8000
```

### 3. 启动服务

**启动后端：**
```bash
python -m src.backend.main
```
或
```bash
python backend_run.py
```

**启动前端：**
```bash
streamlit run src/frontend/main.py
```
或
```bash
python frontend_run.py
```

## API 文档

服务启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

```bash
pytest
```

## 环境要求

- Python 3.11+
- PostgreSQL (可选，可使用 Supabase)
