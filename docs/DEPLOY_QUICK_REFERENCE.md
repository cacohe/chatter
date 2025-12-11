# 阿里云部署快速参考

## 快速部署步骤（5分钟）

### 1. 服务器准备（5分钟）

```bash
# 1. 购买阿里云ECS实例
#    - CPU: 2核+
#    - 内存: 4GB+
#    - 系统: Ubuntu 22.04 LTS
#    - 开放端口: 22, 80, 443

# 2. SSH连接到服务器
ssh root@your-server-ip
```

### 2. 一键部署（10分钟）

```bash
# 方式1：使用一键部署脚本（推荐）
wget https://raw.githubusercontent.com/your-repo/chatter/main/scripts/deploy_aliyun.sh
# 或上传脚本到服务器
bash scripts/deploy_aliyun.sh

# 方式2：手动部署
# 参考 docs/DEPLOY_ALIYUN.md
```

### 3. 代码部署（5分钟）

```bash
# 方式1：从Git仓库克隆
cd /opt
git clone <your-repo-url> chatter
cd chatter

# 方式2：使用scp上传（在本地执行）
scp -r /path/to/chatter root@your-server-ip:/opt/

# 配置环境变量
cd /opt/chatter
cp .env.example .env
vim .env  # 填入API密钥
```

### 4. 启动服务（2分钟）

```bash
cd /opt/chatter/docker
docker-compose up -d

# 验证服务
docker-compose ps
curl http://localhost:8000/docs
```

### 5. 配置Nginx（5分钟）

```bash
# 编辑Nginx配置
vim /etc/nginx/sites-available/chatter
# 或
vim /etc/nginx/conf.d/chatter.conf

# 测试并重载
nginx -t
systemctl reload nginx
```

### 6. 配置域名和HTTPS（10分钟）

```bash
# 1. 在阿里云域名控制台添加A记录
#    api.yourdomain.com -> 服务器IP
#    chat.yourdomain.com -> 服务器IP

# 2. 安装Certbot
apt install -y certbot python3-certbot-nginx

# 3. 获取SSL证书
certbot --nginx -d api.yourdomain.com -d chat.yourdomain.com
```

---

## 常用命令

### 服务管理

```bash
# 启动服务
cd /opt/chatter/docker && docker-compose up -d

# 停止服务
cd /opt/chatter/docker && docker-compose down

# 重启服务
cd /opt/chatter/docker && docker-compose restart

# 查看日志
cd /opt/chatter/docker && docker-compose logs -f

# 查看状态
cd /opt/chatter/docker && docker-compose ps
```

### 日志查看

```bash
# 应用日志
tail -f /opt/chatter/logs/app.log

# Docker日志
docker-compose -f /opt/chatter/docker/docker-compose.yml logs -f

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 更新代码

```bash
# 方式1：Git更新
cd /opt/chatter
git pull
cd docker
docker-compose build
docker-compose up -d

# 方式2：重新部署
cd /opt/chatter/docker
docker-compose down
# 上传新代码
docker-compose build --no-cache
docker-compose up -d
```

---

## 检查清单

部署前检查：
- [ ] 服务器已购买并配置
- [ ] 安全组端口已开放（22, 80, 443）
- [ ] 已获取服务器IP和SSH访问权限

部署时检查：
- [ ] Docker和Docker Compose已安装
- [ ] 代码已上传到服务器
- [ ] .env文件已配置（至少一个API密钥）
- [ ] 服务已启动（docker-compose ps显示Up）

部署后检查：
- [ ] 可以通过IP访问服务
- [ ] 域名解析已配置
- [ ] Nginx反向代理已配置
- [ ] HTTPS证书已安装
- [ ] 防火墙已配置

---

## 故障排查

### 服务无法访问

```bash
# 1. 检查服务是否运行
docker ps
docker-compose ps

# 2. 检查端口是否监听
netstat -tlnp | grep -E '8000|8501'

# 3. 检查防火墙
ufw status  # Ubuntu
firewall-cmd --list-all  # CentOS

# 4. 检查Nginx配置
nginx -t
systemctl status nginx
```

### Docker问题

```bash
# 检查Docker服务
systemctl status docker

# 重启Docker
systemctl restart docker

# 查看Docker日志
journalctl -u docker -f
```

### 端口冲突

```bash
# 查看端口占用
lsof -i :8000
lsof -i :8501

# 或使用
ss -tlnp | grep -E '8000|8501'
```

---

## 性能优化建议

1. **资源限制**：在docker-compose.yml中设置资源限制
2. **日志轮转**：配置日志自动清理
3. **监控告警**：设置服务监控和告警
4. **定期备份**：配置自动备份脚本
5. **CDN加速**：使用阿里云CDN加速静态资源

---

详细部署指南请参考：[完整部署文档](DEPLOY_ALIYUN.md)

