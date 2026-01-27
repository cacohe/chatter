# 使用纯 Docker 部署指南

本指南介绍如何使用纯 Docker 命令（不使用 docker-compose）部署应用。

## 为什么使用纯 Docker？

- **更轻量**：不需要安装 docker-compose
- **更灵活**：可以精确控制每个容器的配置
- **更简单**：在某些环境中，Docker 是唯一可用的工具
- **学习价值**：更好地理解 Docker 的工作原理

## 快速开始

### 本地部署

1. **确保已安装 Docker**
   ```bash
   docker --version
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入 API 密钥
   ```

3. **运行部署脚本**
   ```bash
   chmod +x scripts/deploy_docker.sh
   ./scripts/deploy_docker.sh
   ```

4. **或使用命令行参数**
   ```bash
   # 构建并启动
   ./scripts/deploy_docker.sh up --build
   
   # 仅启动（不重新构建）
   ./scripts/deploy_docker.sh up
   
   # 停止服务
   ./scripts/deploy_docker.sh down
   
   # 查看日志
   ./scripts/deploy_docker.sh logs
   
   # 查看状态
   ./scripts/deploy_docker.sh status
   ```

### 阿里云服务器部署

1. **上传代码到服务器**
   ```bash
   scp -r /path/to/chatter root@your-server:/opt/chatter
   ```

2. **运行部署脚本**
   ```bash
   sudo bash scripts/deploy_aliyun_docker.sh
   ```

   脚本会自动：
   - 检测操作系统
   - 安装 Docker（如果未安装）
   - 配置 Docker 镜像加速
   - 安装 Nginx
   - 构建并启动服务

## 脚本功能

### deploy_docker.sh（本地部署）

**交互式菜单：**
- 构建并启动服务
- 仅启动服务（不重新构建）
- 停止服务
- 重启服务
- 查看日志
- 查看服务状态
- 清理并重新部署
- 清理所有资源

**命令行模式：**
```bash
./scripts/deploy_docker.sh [命令] [选项]

命令：
  up, start     启动服务
                  选项: --build, -b  重新构建镜像
  down, stop    停止服务
  restart        重启服务
  logs           查看日志
                  参数: backend, frontend, 或不指定（查看所有）
  status, ps     查看服务状态
  build          构建镜像
  clean          清理所有资源
```

### deploy_aliyun_docker.sh（服务器部署）

**自动执行：**
1. 检测操作系统
2. 安装 Docker（如果未安装）
3. 配置 Docker 镜像加速（阿里云镜像）
4. 安装 Nginx
5. 配置防火墙
6. 设置项目目录
7. 检查环境变量
8. 构建并启动服务
9. 创建 Nginx 配置模板

## 手动部署步骤

如果您想手动执行部署，可以按照以下步骤：

### 1. 创建网络

```bash
docker network create chatter-network
```

### 2. 构建镜像

```bash
# 构建后端镜像
docker build -f docker/Dockerfile -t chatter-backend .

# 构建前端镜像
docker build -f docker/Dockerfile.frontend -t chatter-frontend .
```

### 3. 启动后端容器

```bash
docker run -d \
  --name chatter-backend \
  --network chatter-network \
  --hostname backend \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  -e BACKEND_HOST=0.0.0.0 \
  -e BACKEND_PORT=8000 \
  -e BACKEND_IP=backend \
  -e DASHSCOPE_API_KEY=your_key_here \
  chatter-backend
```

### 4. 等待后端就绪

```bash
# 检查健康状态
docker exec chatter-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs', timeout=5)"
```

### 5. 启动前端容器

```bash
docker run -d \
  --name chatter-frontend \
  --network chatter-network \
  -p 8501:8501 \
  --restart unless-stopped \
  -e BACKEND_IP=backend \
  -e BACKEND_PORT=8000 \
  chatter-frontend
```

## 管理命令

### 查看服务状态

```bash
docker ps --filter "name=chatter-"
```

### 查看日志

```bash
# 查看所有服务日志
docker logs -f chatter-backend chatter-frontend

# 查看后端日志
docker logs -f chatter-backend

# 查看前端日志
docker logs -f chatter-frontend
```

### 停止服务

```bash
docker stop chatter-backend chatter-frontend
```

### 启动服务

```bash
docker start chatter-backend chatter-frontend
```

### 重启服务

```bash
docker restart chatter-backend chatter-frontend
```

### 删除容器

```bash
docker stop chatter-backend chatter-frontend
docker rm chatter-backend chatter-frontend
```

### 删除镜像

```bash
docker rmi chatter-backend chatter-frontend
```

### 删除网络

```bash
docker network rm chatter-network
```

## 环境变量配置

环境变量可以通过以下方式配置：

1. **使用 .env 文件**（推荐）
   - 脚本会自动从 `.env` 文件读取环境变量
   - 后端需要的 API 密钥会自动传递到容器

2. **直接在命令中指定**
   ```bash
   docker run -d \
     --name chatter-backend \
     -e DASHSCOPE_API_KEY=your_key \
     -e OPENAI_API_KEY=your_key \
     ...
   ```

3. **使用环境变量文件**
   ```bash
   docker run -d \
     --name chatter-backend \
     --env-file .env \
     ...
   ```

## 端口配置

默认端口：
- 后端 API: 8000
- 前端界面: 8501

可以通过修改 `.env` 文件或直接修改 `docker run` 命令中的端口映射来更改：

```bash
# 修改后端端口为 9000
-p 9000:8000

# 修改前端端口为 9501
-p 9501:8501
```

## 网络配置

容器使用自定义网络 `chatter-network`，这样：
- 容器可以通过容器名互相访问
- 后端容器的主机名是 `backend`，前端可以通过 `backend:8000` 访问后端
- 网络隔离，更安全

## 数据持久化

日志目录挂载到主机：
```bash
-v $(pwd)/logs:/app/logs
```

这样日志文件会保存在主机的 `logs` 目录中，即使容器删除也不会丢失。

## 健康检查

容器配置了健康检查：

**后端：**
- 检查 `/docs` 端点
- 间隔：30秒
- 超时：10秒
- 重试：3次
- 启动等待：10秒

**前端：**
- 检查 `/_stcore/health` 端点
- 间隔：30秒
- 超时：10秒
- 重试：3次
- 启动等待：10秒

查看健康状态：
```bash
docker inspect --format='{{.State.Health.Status}}' chatter-backend
```

## 故障排查

### 容器无法启动

1. **检查日志**
   ```bash
   docker logs chatter-backend
   docker logs chatter-frontend
   ```

2. **检查端口占用**
   ```bash
   netstat -tulpn | grep -E '8000|8501'
   ```

3. **检查镜像是否存在**
   ```bash
   docker images | grep chatter
   ```

### 前端无法连接后端

1. **检查网络**
   ```bash
   docker network inspect chatter-network
   ```

2. **测试后端连接**
   ```bash
   docker exec chatter-frontend ping backend
   ```

3. **检查后端是否运行**
   ```bash
   docker exec chatter-backend curl http://localhost:8000/docs
   ```

### 环境变量未生效

1. **检查 .env 文件**
   ```bash
   cat .env
   ```

2. **检查容器环境变量**
   ```bash
   docker exec chatter-backend env | grep API_KEY
   ```

3. **重新创建容器**
   ```bash
   docker stop chatter-backend
   docker rm chatter-backend
   # 重新运行启动命令
   ```

## 与 docker-compose 的对比

| 特性 | docker-compose | 纯 Docker |
|------|---------------|-----------|
| 安装要求 | 需要安装 docker-compose | 只需 Docker |
| 配置文件 | docker-compose.yml | 命令行参数 |
| 启动速度 | 较快 | 稍慢（需要手动执行多个命令） |
| 灵活性 | 中等 | 高 |
| 学习曲线 | 简单 | 中等 |
| 适用场景 | 开发、测试、生产 | 生产、CI/CD |

## 最佳实践

1. **使用脚本部署**：推荐使用提供的脚本，而不是手动执行命令
2. **版本标签**：生产环境建议为镜像打标签
   ```bash
   docker build -f docker/Dockerfile -t chatter-backend:v1.0.0 .
   ```
3. **资源限制**：生产环境建议设置资源限制
   ```bash
   --memory="512m" --cpus="1.0"
   ```
4. **日志管理**：配置日志轮转，避免日志文件过大
5. **备份数据**：定期备份日志和配置文件

## 参考

- [Docker 官方文档](https://docs.docker.com/)
- [Docker 网络文档](https://docs.docker.com/network/)
- [Docker 健康检查](https://docs.docker.com/engine/reference/builder/#healthcheck)

