# 快速开始指南

## 方式一：Docker 部署（推荐）

### 1. 准备工作

```bash
# 克隆项目
git clone <repository-url>
cd chatter

# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，至少配置一个 AI 模型的 API 密钥
# 例如：DASHSCOPE_API_KEY=your_key_here
```

### 2. 启动服务

```bash
# 使用 Docker Compose（推荐）
cd docker && docker-compose up -d

# 或使用 Makefile
make up

# 或使用部署脚本

# Linux/Mac 使用 bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Windows 使用 PowerShell（重要：必须使用 PowerShell，不能使用 sh）
.\scripts\deploy.ps1
# 或如果遇到执行策略限制：
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
```

### 3. 访问应用

- 前端界面: http://localhost:8501
- 后端 API 文档: http://localhost:8000/docs

### 4. 查看日志

```bash
# 查看所有服务日志
cd docker && docker-compose logs -f

# 或使用 Makefile
make logs

# 仅查看后端日志
make logs-backend

# 仅查看前端日志
make logs-frontend
```

### 5. 停止服务

```bash
cd docker && docker-compose down

# 或使用 Makefile
make down
```

## 方式二：本地开发部署

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，填入 API 密钥
```

### 3. 启动服务

**终端 1 - 启动后端：**
```bash
python scripts/backend_run.py

# 开发模式（自动重载）
python scripts/backend_run.py --reload
```

**终端 2 - 启动前端：**
```bash
python scripts/frontend_run.py
```

### 4. 访问应用

- 前端界面: http://localhost:8501
- 后端 API 文档: http://localhost:8000/docs

## 环境变量配置

### 必需配置

至少需要配置一个 AI 模型的 API 密钥：

- `DASHSCOPE_API_KEY` - 通义千问
- `OPENAI_API_KEY` - OpenAI
- `GOOGLE_API_KEY` - Google Gemini

### 可选配置

- `SERPER_API_KEY` - 联网搜索功能
- `BING_SUBSCRIPTION_KEY` - Bing 搜索（备选）

## 常见问题

### 1. 端口被占用

如果 8000 或 8501 端口被占用，可以修改 `.env` 文件中的端口配置。

### 2. Docker 容器无法启动

检查日志：
```bash
docker-compose logs backend
docker-compose logs frontend
```

### 3. 前端无法连接后端

确保：
1. 后端服务已启动
2. `.env` 文件中的 `BACKEND_IP` 配置正确
3. 防火墙允许相应端口

### 4. 模型调用失败

1. 检查 API 密钥是否正确
2. 检查网络连接
3. 查看后端日志获取详细错误信息

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 API 文档: http://localhost:8000/docs
- 配置更多模型和工具

