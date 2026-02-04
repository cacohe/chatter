# 多模型AI聊天机器人

一个支持多种大语言模型（LLM）的智能聊天机器人系统，支持模型切换、联网搜索和自定义MCP工具调用。

## 功能特性

- 🤖 **多模型支持**: 支持通义千问、OpenAI、Google Gemini、Ollama 等多种模型
- 🔄 **模型切换**: 运行时动态切换不同的AI模型
- 🔍 **联网搜索**: 集成 Serper 和 Bing 搜索工具，获取实时信息
- 🛠️ **MCP工具**: 支持自定义 MCP (Model Context Protocol) 工具调用
- 💬 **会话管理**: 支持多会话上下文管理和历史记录
- 🎨 **现代化UI**: 基于 Streamlit 的友好用户界面

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: Streamlit
- **AI框架**: LangChain
- **配置管理**: Pydantic
- **容器化**: Docker & Docker Compose

## 项目结构

```
chatter/
├── src/                    # 源代码目录
│   ├── backend/            # 后端服务
│   │   ├── controller/     # 控制器
│   │   ├── manager/        # 管理器（模型、工具、上下文）
│   │   └── main.py         # FastAPI 应用入口
│   ├── frontend/           # 前端服务
│   │   ├── main.py         # Streamlit 应用入口
│   │   └── routes.py       # API 路由封装
│   ├── infra/              # 基础设施（日志等）
│   │   └── log/            # 日志模块
│   ├── config.py           # 配置管理
│   └── __init__.py
├── scripts/                # 脚本目录
│   ├── backend_run.py      # 后端启动脚本
│   ├── frontend_run.py     # 前端启动脚本
│   ├── deploy.sh          # 部署脚本 (Linux/Mac)
│   └── deploy.ps1         # 部署脚本 (Windows)
├── docker/                 # Docker 配置目录
│   ├── Dockerfile          # 后端 Docker 镜像
│   ├── Dockerfile.frontend # 前端 Docker 镜像
│   └── docker-compose.yml  # Docker Compose 配置
├── docs/                   # 文档目录
│   └── QUICKSTART.md       # 快速开始指南
├── tests/                  # 测试目录
│   └── unittest/          # 单元测试
├── requirements.txt        # Python 依赖
├── Makefile                # 便捷命令
├── README.md               # 项目文档（根目录）
└── .env.example            # 环境变量示例
```

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose (可选，用于容器化部署)

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd chatter
```

2. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

5. **启动后端服务**
```bash
python scripts/backend_run.py
# 或使用开发模式（自动重载）
python scripts/backend_run.py --reload
```

6. **启动前端服务**（新终端）
```bash
python scripts/frontend_run.py
```

7. **访问应用**
- 前端界面: http://localhost:8501
- 后端API文档: http://localhost:8000/docs

### Docker 部署

1. **构建并启动服务**
```bash
cd docker && docker-compose up -d
# 或使用 Makefile
make up
```

2. **查看日志**
```bash
cd docker && docker-compose logs -f
# 或使用 Makefile
make logs
```

3. **停止服务**
```bash
cd docker && docker-compose down
# 或使用 Makefile
make down
```

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```env
# 后端服务配置
BACKEND_IP=localhost          # 前端连接的后端地址
BACKEND_HOST=0.0.0.0          # 后端监听地址
BACKEND_PORT=8000             # 后端端口

# AI模型API密钥（至少配置一个）
DASHSCOPE_API_KEY=           # 通义千问 API Key
OPENAI_API_KEY=               # OpenAI API Key
GOOGLE_API_KEY=               # Google Gemini API Key

# 搜索工具API密钥（可选，二选一）
SERPER_API_KEY=               # Serper API Key
BING_SUBSCRIPTION_KEY=        # Bing Search API Key
```

### 支持的模型

- **通义千问** (qwen): 需要 `DASHSCOPE_API_KEY`
- **OpenAI** (openai, openai-4): 需要 `OPENAI_API_KEY`
- **Google Gemini** (gemini): 需要 `GOOGLE_API_KEY`
- **Ollama** (llama, mistral): 需要本地运行 Ollama 服务

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

- `POST /chat` - 发送聊天消息
- `GET /models` - 获取可用模型列表
- `POST /models/switch` - 切换模型
- `GET /tools` - 获取可用工具列表
- `POST /sessions/{session_id}/clear` - 清空会话

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

### 添加新模型

1. 在 `src/backend/manager/model_manager.py` 中添加模型初始化代码
2. 在配置中添加相应的 API 密钥环境变量

### 添加新工具

1. 在 `src/backend/manager/tool_manager.py` 中添加工具实现
2. 在 `src/backend/controller/chat_controller.py` 中添加工具调用逻辑

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

# 启动服务
cd docker && docker-compose up -d

# 查看状态
cd docker && docker-compose ps

# 查看日志
cd docker && docker-compose logs -f backend
cd docker && docker-compose logs -f frontend
```

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

生产环境建议使用环境变量或密钥管理服务（如 AWS Secrets Manager、阿里云密钥管理服务）来管理敏感信息，而不是 `.env` 文件。

## 故障排查

### 后端无法启动

1. 检查端口是否被占用: `netstat -an | grep 8000`
2. 检查环境变量配置是否正确
3. 查看日志: `logs/app.log`

### 前端无法连接后端

1. 确认后端服务已启动
2. 检查 `BACKEND_IP` 配置是否正确
3. 检查防火墙设置

### 模型调用失败

1. 检查 API 密钥是否正确配置
2. 检查网络连接
3. 查看后端日志获取详细错误信息

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

[添加许可证信息]

## 联系方式

[添加联系方式]

