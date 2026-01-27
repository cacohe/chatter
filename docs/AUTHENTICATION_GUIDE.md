# 用户认证和数据持久化指南

本文档说明如何使用添加的用户认证和数据持久化功能。

## 功能概述

- ✅ 用户注册和登录（JWT认证）
- ✅ 用户信息存储到PostgreSQL
- ✅ 会话信息持久化
- ✅ 聊天消息持久化
- ✅ API接口认证保护

## 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

#### 选项A：使用Docker Compose（推荐）

```bash
cd docker
docker-compose up -d
```

这将启动以下服务：
- PostgreSQL (端口5432)
- Backend API (端口8000)
- Frontend UI (端口8501)

#### 选项B：手动配置PostgreSQL

1. 安装PostgreSQL
2. 创建数据库：
```sql
CREATE DATABASE chatter;
CREATE USER chatter WITH PASSWORD 'chatter';
GRANT ALL PRIVILEGES ON DATABASE chatter TO chatter;
```

3. 更新 `.env` 文件中的 `DATABASE_URL`

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
# 数据库配置
DATABASE_URL=postgresql://chatter:chatter@localhost:5432/chatter

# JWT配置（生产环境请修改）
JWT_SECRET_KEY=your-random-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI模型API密钥
DASHSCOPE_API_KEY=your-api-key
# 或
OPENAI_API_KEY=your-api-key
```

## API 使用说明

### 1. 用户注册

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

### 2. 用户登录

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**响应：** 同注册响应

### 3. 刷新Token

```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 4. 获取当前用户信息

```bash
GET /auth/me
Authorization: Bearer <access_token>
```

### 5. 发送聊天消息（需要认证）

```bash
POST /chat/message
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "你好，请介绍一下你自己",
  "session_id": null,  // 可选，不提供则创建新会话
  "use_tools": true,
  "temperature": 0.7
}
```

**响应：**
```json
{
  "response": "你好！我是...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "tools_used": false,
  "tool_result": "",
  "model_used": "qwen"
}
```

### 6. 获取用户会话列表

```bash
GET /sessions?skip=0&limit=100
Authorization: Bearer <access_token>
```

**响应：**
```json
[
  {
    "id": 1,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": 1,
    "title": "新对话",
    "model_name": "qwen",
    "created_at": "2026-01-27T00:00:00",
    "updated_at": "2026-01-27T00:00:00"
  }
]
```

### 7. 获取会话详情

```bash
GET /sessions/{session_id}
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": 1,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "新对话",
  "model_name": "qwen",
  "created_at": "2026-01-27T00:00:00",
  "updated_at": "2026-01-27T00:00:00",
  "messages": [
    {
      "id": 1,
      "role": "system",
      "content": "你是一个有帮助的AI助手...",
      "model_used": null,
      "created_at": "2026-01-27T00:00:00"
    },
    {
      "id": 2,
      "role": "user",
      "content": "你好",
      "model_used": "qwen",
      "created_at": "2026-01-27T00:00:00"
    }
  ]
}
```

### 8. 删除会话

```bash
DELETE /sessions/{session_id}
Authorization: Bearer <access_token>
```

### 9. 清空会话历史

```bash
POST /chat/sessions/{session_id}/clear
Authorization: Bearer <access_token>
```

## 数据库结构

### users 表
- id (主键)
- username (唯一)
- email (唯一)
- hashed_password
- full_name
- is_active
- created_at
- updated_at

### sessions 表
- id (主键)
- session_id (唯一)
- user_id (外键)
- title
- system_prompt
- model_name
- created_at
- updated_at

### messages 表
- id (主键)
- session_id (外键)
- role (system/user/assistant/tool)
- content
- tool_calls (JSON)
- tool_result
- model_used
- temperature
- created_at

## 测试API

使用 curl 测试：

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

# 3. 发送消息
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'

# 4. 获取会话列表
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN"
```

## 注意事项

1. **安全性**：生产环境务必修改 `JWT_SECRET_KEY`
2. **密码**：使用 bcrypt 加密存储
3. **会话管理**：默认保留最近10轮对话
4. **数据库备份**：定期备份PostgreSQL数据
5. **日志记录**：查看 `logs/` 目录下的应用日志

## 故障排查

### 数据库连接失败
- 检查PostgreSQL是否运行
- 验证 `DATABASE_URL` 配置
- 确认数据库用户权限

### Token无效
- 检查token是否过期
- 验证 `JWT_SECRET_KEY` 配置
- 使用刷新token获取新的access token

### 会话未找到
- 确认session_id正确
- 检查是否登录了正确的用户
- 验证会话权限

## 更多信息

- API文档：http://localhost:8000/docs
- 项目README：../README.md
