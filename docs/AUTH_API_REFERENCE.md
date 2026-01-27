# 认证和会话API参考

## 认证 API (`/auth`)

### POST /auth/register
用户注册

**请求体：**
```json
{
  "username": "string (3-50字符)",
  "email": "string (有效邮箱)",
  "password": "string (最少6字符)",
  "full_name": "string (可选)"
}
```

**响应：**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "is_active": "boolean"
  }
}
```

**状态码：**
- 201: 注册成功
- 400: 用户名或邮箱已存在
- 422: 请求参数验证失败

---

### POST /auth/login
用户登录

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应：** 同注册接口

**状态码：**
- 200: 登录成功
- 401: 用户名或密码错误
- 403: 账户被禁用
- 422: 请求参数验证失败

---

### POST /auth/refresh
刷新访问令牌

**请求体：**
```json
{
  "refresh_token": "string"
}
```

**响应：**
```json
{
  "access_token": "string"
}
```

**状态码：**
- 200: 刷新成功
- 401: 刷新令牌无效或过期
- 422: 请求参数验证失败

---

### GET /auth/me
获取当前用户信息

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**状态码：**
- 200: 成功
- 401: 未认证或令牌无效

---

## 会话管理 API (`/sessions`)

### GET /sessions
获取当前用户的会话列表

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `skip`: 跳过数量（默认0）
- `limit`: 返回数量（默认100，最大100）

**响应：**
```json
[
  {
    "id": "integer",
    "session_id": "string",
    "user_id": "integer",
    "title": "string",
    "model_name": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

**状态码：**
- 200: 成功
- 401: 未认证

---

### GET /sessions/{session_id}
获取会话详情（包含所有消息）

**请求头：**
```
Authorization: Bearer <access_token>
```

**路径参数：**
- `session_id`: 会话ID

**响应：**
```json
{
  "id": "integer",
  "session_id": "string",
  "user_id": "integer",
  "title": "string",
  "model_name": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": [
    {
      "id": "integer",
      "role": "system|user|assistant|tool",
      "content": "string",
      "model_used": "string|null",
      "temperature": "string|null",
      "created_at": "datetime"
    }
  ]
}
```

**状态码：**
- 200: 成功
- 401: 未认证
- 403: 无权访问
- 404: 会话不存在

---

### DELETE /sessions/{session_id}
删除会话（包括所有消息）

**请求头：**
```
Authorization: Bearer <access_token>
```

**路径参数：**
- `session_id`: 会话ID

**响应：**
```json
{
  "success": true,
  "message": "会话已删除"
}
```

**状态码：**
- 200: 删除成功
- 401: 未认证
- 403: 无权删除
- 404: 会话不存在

---

## 聊天 API (`/chat`)

### POST /chat/message
发送聊天消息

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "message": "string (用户输入)",
  "session_id": "string|null (会话ID，不提供则创建新会话)",
  "use_tools": "boolean (是否使用工具，默认true)",
  "temperature": "number (0-2，默认0.7)"
}
```

**响应：**
```json
{
  "response": "string (AI回复)",
  "session_id": "string",
  "tools_used": "boolean",
  "tool_result": "string",
  "model_used": "string"
}
```

**状态码：**
- 200: 成功
- 401: 未认证
- 500: 服务器错误

---

### POST /chat/models/switch
切换AI模型

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "model_name": "string (qwen|openai|openai-4|gemini|llama|mistral)"
}
```

**响应：**
```json
{
  "success": true,
  "current_model": "string"
}
```

**状态码：**
- 200: 成功
- 401: 未认证

---

### GET /chat/models
获取可用模型列表

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "models": ["qwen", "openai", "openai-4", "gemini", "llama", "mistral"]
}
```

**状态码：**
- 200: 成功
- 401: 未认证

---

### GET /chat/tools
获取可用工具列表

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "网络搜索工具"
    },
    {
      "name": "weather",
      "description": "天气查询工具"
    }
  ]
}
```

**状态码：**
- 200: 成功
- 401: 未认证

---

### POST /chat/sessions/{session_id}/clear
清空会话历史

**请求头：**
```
Authorization: Bearer <access_token>
```

**路径参数：**
- `session_id`: 会话ID

**响应：**
```json
{
  "success": true,
  "message": "会话历史已清空"
}
```

**状态码：**
- 200: 成功
- 401: 未认证
- 403: 无权操作
- 404: 会话不存在

---

## 其他 API

### GET /
根端点

**响应：**
```json
{
  "message": "多模型AI聊天机器人 API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### GET /health
健康检查

**响应：**
```json
{
  "status": "healthy"
}
```

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

常见错误状态码：
- 400: 请求参数错误
- 401: 未认证或令牌无效
- 403: 权限不足
- 404: 资源不存在
- 422: 请求体验证失败
- 500: 服务器内部错误

---

## 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 注册
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

# 2. 设置认证头
headers = {"Authorization": f"Bearer {token}"}

# 3. 发送消息
response = requests.post(
    f"{BASE_URL}/chat/message",
    headers=headers,
    json={"message": "你好"}
)
print(response.json()["response"])

# 4. 获取会话
response = requests.get(
    f"{BASE_URL}/sessions",
    headers=headers
)
print(response.json())
```

### JavaScript示例

```javascript
const BASE_URL = "http://localhost:8000";

async function chat(message) {
  // 获取token（假设已登录）
  const token = localStorage.getItem("access_token");

  // 发送消息
  const response = await fetch(`${BASE_URL}/chat/message`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message })
  });

  const data = await response.json();
  return data.response;
}
```
