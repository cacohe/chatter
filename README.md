# 多模型AI聊天机器人

一个支持多种大语言模型（LLM）的智能聊天机器人系统，支持模型切换、联网搜索、自定义MCP工具调用，以及完整的用户认证和数据持久化功能。

## 功能特性

### 核心功能
- 🤖 **多模型支持**: 支持通义千问、OpenAI、Google Gemini、Ollama 等多种模型
- 🔄 **模型切换**: 运行时动态切换不同的AI模型
- 🔍 **联网搜索**: 集成 Serper 和 Bing 搜索工具，获取实时信息
- 🛠️ **MCP工具**: 支持自定义 MCP (Model Context Protocol) 工具调用
- 🔐 **用户认证**: JWT令牌认证，支持用户注册和登录
- 👤 **用户管理**: 完整的用户信息管理和权限控制
- 💾 **数据持久化**: 使用PostgreSQL存储用户、会话和聊天消息
- 📝 **会话管理**: 支持多会话管理，会话历史可查询、可删除
- 🔒 **API保护**: 所有聊天相关API都需要认证，确保数据安全

### 其他特性
- 💬 **会话上下文**: 支持会话上下文管理和历史记录
- 🎨 **现代化UI**: 基于 Streamlit 的友好用户界面

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: Streamlit
- **AI框架**: LangChain
- **数据库**: PostgreSQL + SQLAlchemy ORM
- **认证**: JWT (JSON Web Tokens) + bcrypt
- **配置管理**: Pydantic
- **容器化**: Docker & Docker Compose

## 项目结构

```
chatter/
├── src/                      # 源代码目录
│   ├── backend/              # 后端服务
│   │   ├── controller/       # 控制器
│   │   │   ├── auth_controller.py      # 认证控制器
│   │   │   ├── db_chat_controller.py   # 数据库聊天控制器
│   │   │   └── chat_controller.py     # 原有聊天控制器
│   │   ├── manager/          # 管理器（模型、工具、上下文）
│   │   │   ├── db_context_manager.py   # 数据库上下文管理器
│   │   │   └── context_manager.py      # 原有上下文管理器
│   │   ├── models/           # 数据库模型
│   │   │   ├── user.py               # 用户模型
│   │   │   ├── session.py            # 会话模型
│   │   │   └── message.py            # 消息模型
│   │   ├── repository/       # 数据访问层
│   │   │   ├── base_repository.py    # 基础Repository
│   │   │   ├── user_repository.py    # 用户Repository
│   │   │   ├── session_repository.py # 会话Repository
│   │   │   └── message_repository.py # 消息Repository
│   │   ├── routes/           # API路由
│   │   │   ├── auth.py       # 认证路由
│   │   │   ├── session.py    # 会话路由
│   │   │   └── chat.py       # 聊天路由
│   │   ├── schemas/          # Pydantic schemas
│   │   │   ├── auth.py       # 认证数据模型
│   │   │   └── session.py    # 会话数据模型
│   │   ├── database.py       # 数据库连接管理
│   │   ├── security.py       # JWT和密码加密
│   │   ├── dependencies.py   # FastAPI依赖注入
│   │   └── main.py           # FastAPI 应用入口
│   ├── frontend/             # 前端服务
│   │   ├── main.py           # Streamlit 应用入口
│   │   └── routes.py         # API 路由封装
│   ├── infra/                # 基础设施（日志等）
│   │   └── log/              # 日志模块
│   ├── config.py             # 配置管理
│   └── __init__.py
├── scripts/                  # 脚本目录
│   ├── backend_run.py        # 后端启动脚本
│   ├── frontend_run.py       # 前端启动脚本
│   ├── deploy.sh             # 部署脚本 (Linux/Mac)
│   └── deploy.ps1            # 部署脚本 (Windows)
├── docker/                   # Docker 配置目录
│   ├── Dockerfile            # 后端 Docker 镜像
│   ├── Dockerfile.frontend   # 前端 Docker 镜像
│   └── docker-compose.yml    # Docker Compose 配置（包含PostgreSQL）
├── docs/                     # 文档目录
│   ├── QUICKSTART.md         # 快速开始指南
│   ├── AUTHENTICATION_GUIDE.md    # 认证功能使用指南
│   └── AUTH_API_REFERENCE.md      # 认证API参考文档
├── tests/                    # 测试目录
│   └── unittest/             # 单元测试
├── requirements.txt          # Python 依赖
├── Makefile                  # 便捷命令
├── README.md                 # 项目文档（根目录）
└── .env.example              # 环境变量示例
```

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+ (可选，Docker会自动提供)
- Docker & Docker Compose (可选，用于容器化部署)

### Docker 部署（推荐）

**最简单的方式，无需手动安装依赖和数据库**

1. **克隆项目**
```bash
git clone <repository-url>
cd chatter
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

3. **启动所有服务**
```bash
cd docker && docker-compose up -d
```

这将自动启动：
- PostgreSQL 数据库
- 后端 API 服务
- 前端 UI 服务

4. **访问应用**
- 前端界面: http://localhost:8501
- 后端API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 本地开发

**适用于需要修改代码的开发场景**

1. **安装 PostgreSQL**

确保已安装 PostgreSQL 15+，或使用Docker运行：
```bash
docker run -d --name chatter-postgres \
  -e POSTGRES_USER=chatter \
  -e POSTGRES_PASSWORD=chatter \
  -e POSTGRES_DB=chatter \
  -p 5432:5432 \
  postgres:15-alpine
```

2. **克隆项目**
```bash
git clone <repository-url>
cd chatter
```

3. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. **安装依赖**
```bash
pip install -r requirements.txt
```

5. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和API密钥
```

6. **启动后端服务**
```bash
python scripts/backend_run.py
# 或使用开发模式（自动重载）
python scripts/backend_run.py --reload
```

7. **启动前端服务**（新终端）
```bash
python scripts/frontend_run.py
```

8. **访问应用**
- 前端界面: http://localhost:8501
- 后端API文档: http://localhost:8000/docs

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```env
# ============================================
# 后端服务配置
# ============================================
BACKEND_IP=localhost          # 前端连接的后端地址
BACKEND_HOST=0.0.0.0          # 后端监听地址
BACKEND_PORT=8000             # 后端端口

# ============================================
# 数据库配置
# ============================================
# PostgreSQL数据库连接URL
DATABASE_URL=postgresql://chatter:chatter@localhost:5432/chatter

# 是否输出SQL日志（开发环境可设为true）
DATABASE_ECHO=false

# ============================================
# JWT认证配置
# ============================================
# JWT密钥（生产环境请务必修改为随机字符串）
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# JWT加密算法
JWT_ALGORITHM=HS256

# 访问令牌过期时间（分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 刷新令牌过期时间（天）
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# AI模型API密钥（至少配置一个）
# ============================================
DASHSCOPE_API_KEY=           # 通义千问 API Key
OPENAI_API_KEY=               # OpenAI API Key
GOOGLE_API_KEY=               # Google Gemini API Key

# ============================================
# 搜索工具API密钥（可选，二选一）
# ============================================
SERPER_API_KEY=               # Serper API Key (推荐)
BING_SUBSCRIPTION_KEY=        # Bing Search API Key
```

### 支持的模型

- **通义千问** (qwen): 需要 `DASHSCOPE_API_KEY`
- **OpenAI** (openai, openai-4): 需要 `OPENAI_API_KEY`
- **Google Gemini** (gemini): 需要 `GOOGLE_API_KEY`
- **Ollama** (llama, mistral): 需要本地运行 Ollama 服务

## 认证功能使用

### 用户注册和登录

系统提供完整的用户认证功能，支持用户注册和JWT令牌登录。

#### 1. 用户注册

```bash
POST /auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "测试用户"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "测试用户",
    "is_active": true
  }
}
```

#### 2. 用户登录

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

#### 3. 使用认证

所有聊天相关的API都需要在请求头中包含认证令牌：

```bash
Authorization: Bearer <access_token>
```

### 完整使用示例

```bash
# 1. 注册用户
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 2. 登录获取token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.access_token')

# 3. 发送聊天消息（需要认证）
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'

# 4. 获取会话列表
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN"

# 5. 获取会话详情
curl -X GET http://localhost:8000/sessions/{session_id} \
  -H "Authorization: Bearer $TOKEN"
```

### 详细文档

更多认证和API使用说明，请参考：
- [认证功能使用指南](docs/AUTHENTICATION_GUIDE.md)
- [认证API参考文档](docs/AUTH_API_REFERENCE.md)

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

#### 认证相关
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新访问令牌
- `GET /auth/me` - 获取当前用户信息

#### 会话管理
- `GET /sessions` - 获取当前用户的会话列表
- `GET /sessions/{session_id}` - 获取会话详情（包含所有消息）
- `DELETE /sessions/{session_id}` - 删除会话

#### 聊天相关
- `POST /chat/message` - 发送聊天消息（需要认证）
- `POST /chat/models/switch` - 切换模型（需要认证）
- `GET /chat/models` - 获取可用模型列表（需要认证）
- `GET /chat/tools` - 获取可用工具列表（需要认证）
- `POST /chat/sessions/{session_id}/clear` - 清空会话历史（需要认证）

#### 其他
- `GET /` - 根端点
- `GET /health` - 健康检查

## 数据库结构

系统使用PostgreSQL存储数据，主要包含以下表：

### users（用户表）
- id (主键)
- username (唯一)
- email (唯一)
- hashed_password (bcrypt加密)
- full_name
- is_active
- created_at
- updated_at

### sessions（会话表）
- id (主键)
- session_id (唯一)
- user_id (外键 -> users.id)
- title
- system_prompt
- model_name
- created_at
- updated_at

### messages（消息表）
- id (主键)
- session_id (外键 -> sessions.id)
- role (system/user/assistant/tool)
- content
- tool_calls (JSON)
- tool_result
- model_used
- temperature
- created_at

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
# 使用 black 格式化代码
black src/

# 使用 isort 整理导入
isort src/
```

### 数据库迁移

当前版本使用SQLAlchemy自动创建表，未来可以集成Alembic进行数据库版本管理：

```python
# 初始化数据库
from src.backend.database import init_db
init_db()

# 创建所有表（开发时使用）
```

### 添加新模型

1. 在 `src/backend/manager/model_manager.py` 中添加模型初始化代码
2. 在配置中添加相应的 API 密钥环境变量

### 添加新工具

1. 在 `src/backend/manager/tool_manager.py` 中添加工具实现
2. 在 `src/backend/controller/db_chat_controller.py` 中添加工具调用逻辑

### 扩展认证功能

系统设计支持以下扩展：
- 添加第三方登录（OAuth2、微信等）
- 添加邮箱验证
- 添加密码重置功能
- 添加角色和权限管理（RBAC）

## 生产部署

### 阿里云服务器部署

详细的阿里云服务器部署指南请参考：[阿里云部署指南](docs/DEPLOY_ALIYUN.md)

**快速部署：**
```bash
# 在服务器上执行一键部署脚本
bash scripts/deploy_aliyun.sh
```

### 使用 Docker Compose

项目已包含完整的 Docker 配置，支持一键部署：

```bash
# 构建镜像
cd docker && docker-compose build

# 启动服务（包括PostgreSQL）
cd docker && docker-compose up -d

# 查看状态
cd docker && docker-compose ps

# 查看日志
cd docker && docker-compose logs -f
```

**服务组成：**
- postgres: PostgreSQL 15 数据库
- backend: FastAPI 后端服务
- frontend: Streamlit 前端服务

### 使用 Makefile

```bash
# 构建镜像
make build

# 启动服务
make up

# 停止服务
make down

# 查看日志
make logs
```

### 环境变量配置

生产环境建议：
1. 使用环境变量或密钥管理服务（如 AWS Secrets Manager、阿里云KMS）管理敏感信息
2. 务必修改 `JWT_SECRET_KEY` 为强随机字符串
3. 配置数据库密码为强密码
4. 启用HTTPS（使用Nginx或Traefik反向代理）
5. 配置防火墙规则，只开放必要端口

### 安全建议

1. **JWT密钥**: 生产环境务必使用强随机字符串
2. **数据库加密**: 启用PostgreSQL的SSL连接
3. **API限流**: 添加速率限制防止滥用
4. **日志审计**: 记录所有认证和授权操作
5. **定期备份**: 定期备份PostgreSQL数据库
6. **密码策略**: 要求用户使用强密码

## 故障排查

### 数据库相关

**数据库连接失败**
- 检查PostgreSQL是否运行: `docker ps | grep postgres`
- 验证 `DATABASE_URL` 配置是否正确
- 确认数据库用户权限
- 查看后端日志获取详细错误信息

### 认证相关

**Token无效或过期**
- 检查token是否过期（默认30分钟）
- 使用刷新token获取新的access token
- 验证 `JWT_SECRET_KEY` 配置一致性
- 确认前端正确携带认证头

**用户注册失败**
- 检查用户名和邮箱是否已被使用
- 验证密码长度（最少6字符）
- 查看后端日志获取详细错误信息

### 后端无法启动

1. 检查端口是否被占用: `netstat -an | grep 8000`
2. 检查环境变量配置是否正确
3. 查看日志: `logs/app.log`
4. 确认数据库连接正常

### 前端无法连接后端

1. 确认后端服务已启动
2. 检查 `BACKEND_IP` 配置是否正确
3. 检查防火墙设置
4. 查看浏览器控制台的网络请求

### 模型调用失败

1. 检查 API 密钥是否正确配置
2. 检查网络连接
3. 查看后端日志获取详细错误信息
4. 确认API配额是否充足

## 性能优化

### 数据库优化
- 为常用查询字段添加索引
- 配置连接池大小
- 定期清理历史消息
- 启用查询缓存

### API优化
- 添加请求缓存
- 实现响应压缩
- 使用异步I/O
- 添加CDN加速

## 贡献指南

欢迎提交 Issue 和 Pull Request！

在提交代码前，请确保：
1. 代码通过所有测试
2. 代码符合项目风格规范
3. 添加必要的注释和文档
4. 更新相关的文档

## 许可证

[添加许可证信息]

## 联系方式

[添加联系方式]

## 相关文档

- [认证功能使用指南](docs/AUTHENTICATION_GUIDE.md) - 详细的认证功能使用说明
- [认证API参考文档](docs/AUTH_API_REFERENCE.md) - 完整的API接口参考
- [Docker部署指南](docs/DEPLOY_WITH_DOCKER.md) - Docker容器化部署
- [阿里云部署指南](docs/DEPLOY_ALIYUN.md) - 阿里云服务器部署
- [故障排查指南](docs/DOCKER_TROUBLESHOOTING.md) - 常见问题解决
