# 修复 curl HTTP/2 协议错误

## 问题描述

在安装 Docker Compose 时遇到以下错误：
```
curl: (92) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR (err 1)
```

## 解决方案

### 方法一：使用修复后的脚本（推荐）

直接运行修复后的部署脚本：
```bash
bash scripts/deploy_aliyun.sh
```

### 方法二：手动安装 Docker Compose

如果脚本仍然失败，可以手动执行以下命令：

```bash
# 方法 2.1：使用 HTTP/1.1 协议（推荐）
curl --http1.1 -L --retry 3 --retry-delay 5 --connect-timeout 30 --max-time 300 \
  "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

# 方法 2.2：如果 GitHub 访问困难，使用国内镜像源
curl --http1.1 -L --retry 3 --retry-delay 5 \
  "https://get.daocloud.io/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

# 方法 2.3：使用固定版本（如果最新版本获取失败）
COMPOSE_VERSION="v2.24.0"
curl --http1.1 -L --retry 3 --retry-delay 5 \
  "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 创建软链接
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 验证安装
docker-compose --version
```

### 方法三：使用包管理器安装（最简单）

如果您的系统支持，可以直接使用包管理器安装：

**Ubuntu/Debian:**
```bash
apt update
apt install -y docker-compose-plugin
```

**CentOS/RHEL:**
```bash
yum install -y docker-compose-plugin
```

安装后使用 `docker compose`（注意是空格，不是连字符）而不是 `docker-compose`。

## 参数说明

- `--http1.1`: 强制使用 HTTP/1.1 协议，避免 HTTP/2 协议错误
- `--retry 3`: 失败时自动重试 3 次
- `--retry-delay 5`: 每次重试前等待 5 秒
- `--connect-timeout 30`: 连接超时时间 30 秒
- `--max-time 300`: 总超时时间 300 秒（5 分钟）

## 常见问题

### Q: 仍然下载失败怎么办？
A: 尝试以下方法：
1. 检查网络连接
2. 使用 VPN 或代理
3. 使用国内镜像源（如 daocloud.io）
4. 手动下载文件后上传到服务器

### Q: 如何手动下载并上传？
A: 
1. 在本地浏览器访问：`https://github.com/docker/compose/releases/latest`
2. 下载对应系统的文件（如 `docker-compose-linux-x86_64`）
3. 使用 scp 上传到服务器：
   ```bash
   scp docker-compose-linux-x86_64 user@server:/usr/local/bin/docker-compose
   ```
4. 在服务器上添加执行权限：
   ```bash
   chmod +x /usr/local/bin/docker-compose
   ```

