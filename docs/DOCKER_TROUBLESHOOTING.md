# Docker 镜像拉取问题排查指南

## 问题：Docker 镜像拉取失败

### 错误信息
```
pull access denied, repository does not exist or may require authorization
insufficient_scope: authorization failed
```

## 解决方案

### 方案1：配置 Docker 镜像加速（推荐）

在服务器上执行以下命令：

```bash
# 1. 创建或编辑 Docker 配置文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 2. 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 3. 验证配置
docker info | grep -A 10 "Registry Mirrors"
```

### 方案2：使用国内镜像源（已更新到 Dockerfile）

Dockerfile 已更新为使用阿里云镜像源：
- `registry.cn-hangzhou.aliyuncs.com/acs/python:3.11-slim`

如果仍有问题，可以手动拉取镜像：

```bash
# 手动拉取基础镜像
docker pull registry.cn-hangzhou.aliyuncs.com/acs/python:3.11-slim

# 或者使用官方镜像（如果网络允许）
docker pull python:3.11-slim
```

### 方案3：使用代理（如果服务器有代理）

```bash
# 配置 Docker 代理
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf <<-'EOF'
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 方案4：检查网络连接

```bash
# 测试 Docker Hub 连接
curl -I https://registry-1.docker.io/v2/

# 测试阿里云镜像连接
curl -I https://registry.cn-hangzhou.aliyuncs.com/v2/

# 测试 DNS
nslookup registry-1.docker.io
```

## 验证修复

```bash
# 1. 检查 Docker 镜像加速配置
docker info | grep -A 10 "Registry Mirrors"

# 2. 测试拉取镜像
docker pull python:3.11-slim

# 3. 重新构建
cd /opt/chatter/docker
docker-compose build
```

## 其他常见问题

### 问题：docker-compose version 警告

**解决：** 已从 docker-compose.yml 中移除 `version: '3.8'`（新版本不需要）

### 问题：pip 安装慢

**解决：** Dockerfile 中已配置使用阿里云 pip 镜像源

### 问题：构建超时

```bash
# 增加构建超时时间
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300

# 或使用
docker-compose build --timeout 300
```

## 快速修复脚本

```bash
#!/bin/bash
# 快速修复 Docker 镜像加速配置

echo "配置 Docker 镜像加速..."

# 备份原配置
if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
fi

# 创建新配置
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker
systemctl daemon-reload
systemctl restart docker

echo "Docker 镜像加速配置完成！"
echo "验证配置："
docker info | grep -A 10 "Registry Mirrors"
```

