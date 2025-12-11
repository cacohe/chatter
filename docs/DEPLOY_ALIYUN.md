# 阿里云服务器部署指南

本指南将帮助您将多模型AI聊天机器人项目完整部署到阿里云服务器上。

## 目录

1. [服务器准备](#1-服务器准备)
2. [环境配置](#2-环境配置)
3. [代码部署](#3-代码部署)
4. [服务启动](#4-服务启动)
5. [域名和反向代理](#5-域名和反向代理)
6. [安全配置](#6-安全配置)
7. [监控和维护](#7-监控和维护)
8. [故障排查](#8-故障排查)

---

## 1. 服务器准备

### 1.1 购买和配置阿里云服务器

1. **购买ECS实例**
   - 登录阿里云控制台
   - 选择 ECS（弹性计算服务）
   - 推荐配置：
     - CPU: 2核或以上
     - 内存: 4GB或以上
     - 系统盘: 40GB或以上
     - 操作系统: Ubuntu 22.04 LTS 或 CentOS 7/8
     - 网络: 公网IP（必需）

2. **安全组配置**
   - 开放端口：
     - `22` (SSH)
     - `80` (HTTP)
     - `443` (HTTPS)
     - `8000` (后端API，可选，建议通过Nginx反向代理)
     - `8501` (前端，可选，建议通过Nginx反向代理)

3. **获取服务器信息**
   ```bash
   # 记录以下信息：
   - 公网IP地址
   - 用户名（通常是 root 或 ubuntu）
   - SSH密钥或密码
   ```

### 1.2 连接到服务器

```bash
# 使用SSH连接
ssh root@your-server-ip

# 或使用密钥
ssh -i your-key.pem root@your-server-ip
```

---

## 2. 环境配置

### 2.1 系统更新

```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 2.2 安装基础工具

```bash
# Ubuntu/Debian
apt install -y git curl wget vim

# CentOS/RHEL
yum install -y git curl wget vim
```

### 2.3 安装 Docker 和 Docker Compose

#### 安装 Docker

```bash
# 卸载旧版本（如果有）
apt remove docker docker-engine docker.io containerd runc 2>/dev/null || yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null

# 安装依赖
apt install -y ca-certificates curl gnupg lsb-release  # Ubuntu
# 或
yum install -y yum-utils  # CentOS

# 添加Docker官方GPG密钥
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg  # Ubuntu
# 或
yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo  # CentOS

# 安装Docker Engine
apt install -y docker-ce docker-ce-cli containerd.io  # Ubuntu
# 或
yum install -y docker-ce docker-ce-cli containerd.io  # CentOS

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
```

#### 安装 Docker Compose

```bash
# 下载Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 创建软链接（可选）
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# 验证安装
docker-compose --version
```

### 2.4 配置Docker镜像加速（阿里云）

```bash
# 创建或编辑Docker配置文件
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启Docker服务
systemctl daemon-reload
systemctl restart docker
```

### 2.5 安装 Nginx（用于反向代理和HTTPS）

```bash
# Ubuntu/Debian
apt install -y nginx

# CentOS/RHEL
yum install -y nginx

# 启动Nginx
systemctl start nginx
systemctl enable nginx

# 验证安装
nginx -v
```

---

## 3. 代码部署

### 3.1 创建应用目录

```bash
# 创建项目目录
mkdir -p /opt/chatter
cd /opt/chatter
```

### 3.2 克隆项目代码

```bash
# 方式1：从Git仓库克隆（推荐）
git clone <your-repository-url> .

# 方式2：使用scp上传代码
# 在本地执行：
# scp -r /path/to/chatter root@your-server-ip:/opt/chatter

# 方式3：使用rsync上传
# 在本地执行：
# rsync -avz --exclude '__pycache__' --exclude '*.pyc' /path/to/chatter/ root@your-server-ip:/opt/chatter/
```

### 3.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

**重要配置项：**

```env
# 后端服务配置
BACKEND_IP=your-server-ip  # 或使用域名
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# AI模型API密钥（至少配置一个）
DASHSCOPE_API_KEY=your_dashscope_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# 搜索工具API密钥
SERPER_API_KEY=your_serper_key
```

### 3.4 验证文件结构

```bash
# 检查关键文件
ls -la
ls -la docker/
ls -la scripts/
ls -la src/
```

---

## 4. 服务启动

### 4.1 使用 Docker Compose 启动（推荐）

```bash
cd /opt/chatter

# 构建镜像
cd docker
docker-compose build

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4.2 验证服务运行

```bash
# 检查容器状态
docker ps

# 检查端口监听
netstat -tlnp | grep -E '8000|8501'

# 测试后端API
curl http://localhost:8000/docs

# 测试前端
curl http://localhost:8501
```

---

## 5. 域名和反向代理

### 5.1 配置域名解析

1. 在阿里云域名控制台添加A记录：
   - 记录类型：A
   - 主机记录：`api`（后端）和 `chat`（前端）或使用子域名
   - 记录值：服务器公网IP
   - TTL：600

### 5.2 配置 Nginx 反向代理

```bash
# 创建Nginx配置文件
vim /etc/nginx/sites-available/chatter
```

**配置文件内容：**

```nginx
# 后端API配置
server {
    listen 80;
    server_name api.yourdomain.com;  # 替换为您的域名

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# 前端配置
server {
    listen 80;
    server_name chat.yourdomain.com;  # 替换为您的域名

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streamlit特定配置
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 创建软链接（Ubuntu/Debian）
ln -s /etc/nginx/sites-available/chatter /etc/nginx/sites-enabled/

# CentOS/RHEL直接编辑默认配置
# vim /etc/nginx/nginx.conf

# 测试Nginx配置
nginx -t

# 重载Nginx配置
systemctl reload nginx
```

### 5.3 配置 HTTPS（使用 Let's Encrypt）

```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx  # Ubuntu
# 或
yum install -y certbot python3-certbot-nginx  # CentOS

# 获取SSL证书
certbot --nginx -d api.yourdomain.com -d chat.yourdomain.com

# 自动续期测试
certbot renew --dry-run
```

---

## 6. 安全配置

### 6.1 防火墙配置

```bash
# Ubuntu使用ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# CentOS使用firewalld
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 6.2 禁用直接访问后端端口（可选）

```bash
# 修改防火墙，只允许本地访问8000和8501
ufw deny 8000/tcp
ufw deny 8501/tcp
```

### 6.3 配置SSH密钥登录（推荐）

```bash
# 在本地生成密钥对（如果还没有）
ssh-keygen -t rsa -b 4096

# 将公钥复制到服务器
ssh-copy-id root@your-server-ip

# 禁用密码登录（可选，更安全）
vim /etc/ssh/sshd_config
# 设置：PasswordAuthentication no
systemctl restart sshd
```

### 6.4 定期更新系统

```bash
# 设置自动更新（Ubuntu）
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# 或手动更新
apt update && apt upgrade -y  # Ubuntu
yum update -y  # CentOS
```

---

## 7. 监控和维护

### 7.1 设置日志轮转

```bash
# 创建日志轮转配置
cat > /etc/logrotate.d/chatter <<EOF
/opt/chatter/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### 7.2 设置服务自动启动

Docker Compose 服务已经配置了 `restart: unless-stopped`，会自动重启。

### 7.3 监控脚本

```bash
# 创建监控脚本
cat > /opt/chatter/scripts/health_check.sh <<'EOF'
#!/bin/bash

# 检查Docker服务
if ! systemctl is-active --quiet docker; then
    echo "Docker service is down, restarting..."
    systemctl restart docker
fi

# 检查容器状态
cd /opt/chatter/docker
if ! docker-compose ps | grep -q "Up"; then
    echo "Containers are down, restarting..."
    docker-compose up -d
fi
EOF

chmod +x /opt/chatter/scripts/health_check.sh

# 添加到crontab（每5分钟检查一次）
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/chatter/scripts/health_check.sh >> /var/log/chatter-health.log 2>&1") | crontab -
```

### 7.4 备份脚本

```bash
# 创建备份脚本
cat > /opt/chatter/scripts/backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/chatter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份代码
tar -czf $BACKUP_DIR/chatter_$DATE.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    /opt/chatter

# 备份.env文件（重要）
cp /opt/chatter/.env $BACKUP_DIR/.env_$DATE

# 删除7天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name ".env_*" -mtime +7 -delete
EOF

chmod +x /opt/chatter/scripts/backup.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/chatter/scripts/backup.sh") | crontab -
```

---

## 8. 故障排查

### 8.1 常见问题

#### 问题1：无法连接Docker守护进程

```bash
# 检查Docker服务状态
systemctl status docker

# 重启Docker服务
systemctl restart docker

# 检查Docker信息
docker info
```

#### 问题2：端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep -E '8000|8501'

# 或使用ss命令
ss -tlnp | grep -E '8000|8501'

# 杀死占用进程
kill -9 <PID>
```

#### 问题3：容器无法启动

```bash
# 查看容器日志
cd /opt/chatter/docker
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend

# 重启服务
docker-compose restart
```

#### 问题4：Nginx 502错误

```bash
# 检查后端服务是否运行
curl http://localhost:8000/docs

# 检查Nginx错误日志
tail -f /var/log/nginx/error.log

# 检查Nginx配置
nginx -t
```

### 8.2 性能优化

```bash
# 限制容器资源使用（编辑docker-compose.yml）
# 在services下添加：
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 2G
```

### 8.3 日志查看

```bash
# 查看应用日志
tail -f /opt/chatter/logs/app.log

# 查看Docker日志
docker-compose -f /opt/chatter/docker/docker-compose.yml logs -f

# 查看系统日志
journalctl -u docker -f
```

---

## 9. 部署检查清单

- [ ] 服务器已购买并配置
- [ ] 安全组端口已开放
- [ ] Docker和Docker Compose已安装
- [ ] 代码已部署到服务器
- [ ] 环境变量已配置
- [ ] 服务已启动并运行正常
- [ ] 域名解析已配置
- [ ] Nginx反向代理已配置
- [ ] HTTPS证书已配置
- [ ] 防火墙已配置
- [ ] 监控脚本已设置
- [ ] 备份脚本已设置

---

## 10. 快速部署脚本

为了方便部署，可以使用以下一键部署脚本：

```bash
#!/bin/bash
# 一键部署脚本（在服务器上执行）

set -e

echo "开始部署多模型AI聊天机器人..."

# 1. 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

# 2. 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. 安装Nginx
if ! command -v nginx &> /dev/null; then
    echo "安装Nginx..."
    apt install -y nginx || yum install -y nginx
    systemctl start nginx
    systemctl enable nginx
fi

# 4. 创建项目目录
mkdir -p /opt/chatter
cd /opt/chatter

echo "部署完成！"
echo "请执行以下步骤："
echo "1. 将代码上传到 /opt/chatter"
echo "2. 配置 .env 文件"
echo "3. 运行: cd docker && docker-compose up -d"
```

---

## 11. 联系和支持

如遇到问题，请检查：
1. 服务器日志：`/opt/chatter/logs/app.log`
2. Docker日志：`docker-compose logs`
3. Nginx日志：`/var/log/nginx/error.log`

---

**部署完成后，您的服务将可以通过以下地址访问：**
- 前端：`http://chat.yourdomain.com` 或 `https://chat.yourdomain.com`
- 后端API：`http://api.yourdomain.com` 或 `https://api.yourdomain.com`
- API文档：`https://api.yourdomain.com/docs`

