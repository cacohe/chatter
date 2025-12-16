#!/bin/bash

# 阿里云服务器一键部署脚本
# 在服务器上执行此脚本进行快速部署

set -e

echo "=========================================="
echo "多模型AI聊天机器人 - 阿里云部署脚本"
echo "=========================================="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用root用户运行此脚本"
    echo "使用: sudo bash deploy_aliyun.sh"
    exit 1
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        error "无法检测操作系统"
        exit 1
    fi
    info "检测到操作系统: $OS $VER"
}

# 安装Docker
install_docker() {
    if command -v docker &> /dev/null; then
        info "Docker 已安装: $(docker --version)"
        return
    fi
    
    info "安装 Docker..."
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        # 卸载旧版本
        apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # 安装依赖
        apt update
        apt install -y ca-certificates curl gnupg lsb-release
        
        # 添加Docker官方GPG密钥
        install -m 0755 -d /etc/apt/keyrings
        curl --http1.1 -fsSL --retry 3 https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
        
        # 添加Docker仓库
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装Docker
        apt update
        apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        # 卸载旧版本
        yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
        
        # 安装依赖
        yum install -y yum-utils
        
        # 添加Docker仓库
        yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
        
        # 安装Docker
        yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    else
        error "不支持的操作系统: $OS"
        exit 1
    fi
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    # 配置Docker镜像加速
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
    
    systemctl daemon-reload
    systemctl restart docker
    
    info "Docker 安装完成: $(docker --version)"
}

# 安装Nginx
install_nginx() {
    if command -v nginx &> /dev/null; then
        info "Nginx 已安装: $(nginx -v 2>&1)"
        return
    fi
    
    info "安装 Nginx..."
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt install -y nginx
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        yum install -y nginx
    fi
    
    systemctl start nginx
    systemctl enable nginx
    
    info "Nginx 安装完成"
}

# 配置防火墙
configure_firewall() {
    info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
        info "UFW 防火墙已配置"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        info "Firewalld 防火墙已配置"
    else
        warn "未检测到防火墙工具，请手动配置"
    fi
}

# 创建项目目录
setup_project_dir() {
    info "设置项目目录..."
    
    PROJECT_DIR="/opt/chatter"
    mkdir -p $PROJECT_DIR
    mkdir -p $PROJECT_DIR/logs
    
    info "项目目录: $PROJECT_DIR"
    echo ""
    warn "请确保代码已部署到 $PROJECT_DIR 目录"
    warn "如果还没有，请执行以下操作："
    echo "  1. 从Git仓库克隆: cd $PROJECT_DIR && git clone <repo-url> ."
    echo "  2. 或使用scp上传代码"
    echo ""
    read -p "代码是否已部署？(y/n): " code_deployed
    
    if [ "$code_deployed" != "y" ] && [ "$code_deployed" != "Y" ]; then
        warn "请先部署代码，然后重新运行此脚本"
        exit 1
    fi
}

# 检查环境变量
check_env() {
    info "检查环境变量配置..."
    
    if [ ! -f /opt/chatter/.env ]; then
        warn ".env 文件不存在"
        if [ -f /opt/chatter/.env.example ]; then
            info "从 .env.example 创建 .env 文件..."
            cp /opt/chatter/.env.example /opt/chatter/.env
            warn "请编辑 /opt/chatter/.env 文件并填入必要的配置"
            read -p "按 Enter 继续（确保已配置环境变量）..."
        else
            error ".env.example 文件不存在"
            exit 1
        fi
    else
        info ".env 文件已存在"
    fi
}

# 构建和启动服务
start_services() {
    info "构建和启动服务..."
    
    cd /opt/chatter/docker
    
    if [ ! -f docker-compose.yml ]; then
        error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 构建镜像
    info "构建Docker镜像..."
    docker compose build
    
    # 启动服务
    info "启动服务..."
    docker compose up -d
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    info "检查服务状态..."
    if ! docker compose ps; then
        error "服务状态检查失败，请确认Docker服务是否正常运行"
        exit 1
    fi

    # 检查服务健康状态
    info "检查服务健康状态..."
    HEALTHY_SERVICES=$(docker compose ps --filter "status=running" --format "table {{.Service}}\t{{.Status}}" | grep -c "healthy" || echo "0")
    TOTAL_SERVICES=$(docker compose config --services | wc -l)

    if [ "$HEALTHY_SERVICES" -eq "$TOTAL_SERVICES" ] && [ "$TOTAL_SERVICES" -gt 0 ]; then
        info "所有服务运行正常 ($HEALTHY_SERVICES/$TOTAL_SERVICES)"
    else
        warn "部分服务未正常运行 ($HEALTHY_SERVICES/$TOTAL_SERVICES)"
        info "详细服务状态:"
        docker compose ps --format "table {{.Service}}\t{{.Status}}"
        # 打印最近的日志信息
        info "最近的服务日志:"
        docker compose logs --tail=20
    fi
    
    info "服务启动完成！"
}

# 创建Nginx配置模板
create_nginx_config() {
    info "创建Nginx配置模板..."
    
    cat > /tmp/chatter-nginx.conf <<'EOF'
# 后端API配置
# 将 api.yourdomain.com 替换为您的实际域名
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# 前端配置
# 将 chat.yourdomain.com 替换为您的实际域名
server {
    listen 80;
    server_name chat.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    if [ -d /etc/nginx/sites-available ]; then
        # Ubuntu/Debian
        cp /tmp/chatter-nginx.conf /etc/nginx/sites-available/chatter
        ln -sf /etc/nginx/sites-available/chatter /etc/nginx/sites-enabled/
    else
        # CentOS/RHEL
        cp /tmp/chatter-nginx.conf /etc/nginx/conf.d/chatter.conf
    fi
    
    warn "Nginx配置已创建，请编辑配置文件并替换域名："
    if [ -d /etc/nginx/sites-available ]; then
        echo "  vim /etc/nginx/sites-available/chatter"
    else
        echo "  vim /etc/nginx/conf.d/chatter.conf"
    fi
    echo "然后运行: nginx -t && systemctl reload nginx"
}

# 主函数
main() {
    detect_os
    install_docker
    install_nginx
    configure_firewall
    setup_project_dir
    check_env
    start_services
    create_nginx_config
    
    echo ""
    info "=========================================="
    info "部署完成！"
    info "=========================================="
    echo ""
    info "下一步操作："
    echo "  1. 编辑Nginx配置文件并配置域名"
    echo "  2. 运行: nginx -t && systemctl reload nginx"
    echo "  3. 配置域名DNS解析指向服务器IP"
    echo "  4. 安装SSL证书: certbot --nginx -d your-domain.com"
    echo ""
    info "服务地址："
    echo "  - 后端API: http://localhost:8000"
    echo "  - 前端界面: http://localhost:8501"
    echo "  - API文档: http://localhost:8000/docs"
    echo ""
    info "查看日志："
    echo "  - 应用日志: tail -f /opt/chatter/logs/app.log"
    echo "  - Docker日志: cd /opt/chatter/docker && docker-compose logs -f"
    echo ""
}

# 运行主函数
main

