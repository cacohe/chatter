#!/bin/bash

# 生产环境部署脚本
set -e

echo "=========================================="
echo "多模型AI聊天机器人 - 部署脚本"
echo "=========================================="

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未安装 Docker Compose，请先安装 Docker Compose"
    exit 1
fi

# 检查 Docker 守护进程是否运行
echo "检查 Docker 守护进程..."
if ! docker version &> /dev/null; then
    echo ""
    echo "错误: Docker 守护进程未运行！"
    echo "请启动 Docker Desktop 并等待其准备就绪。"
    echo "可以通过运行以下命令检查: docker version"
    exit 1
fi
echo "Docker 守护进程运行正常"

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "警告: 未找到 .env 文件"
    echo "正在从 .env.example 创建 .env 文件..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "请编辑 .env 文件并填入必要的配置"
        read -p "按 Enter 继续..."
    else
        echo "错误: 未找到 .env.example 文件"
        exit 1
    fi
fi

# 选择操作
echo ""
echo "请选择操作:"
echo "1) 构建并启动服务"
echo "2) 仅启动服务（不重新构建）"
echo "3) 停止服务"
echo "4) 重启服务"
echo "5) 查看日志"
echo "6) 清理并重新部署"
read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo "构建并启动服务..."
        cd docker || exit 1
        if ! docker-compose build; then
            echo "构建失败！" >&2
            cd ..
            exit 1
        fi
        if ! docker-compose up -d; then
            echo "启动失败！" >&2
            cd ..
            exit 1
        fi
        cd ..
        echo "服务已启动！"
        echo "后端 API: http://localhost:8000"
        echo "前端界面: http://localhost:8501"
        echo "API文档: http://localhost:8000/docs"
        ;;
    2)
        echo "启动服务..."
        cd docker || exit 1
        if ! docker-compose up -d; then
            echo "启动失败！" >&2
            echo ""
            echo "可能的原因:" >&2
            echo "  1. Docker 守护进程未运行" >&2
            echo "  2. 服务已在运行" >&2
            echo "  3. 端口冲突" >&2
            cd ..
            exit 1
        fi
        cd ..
        echo "服务已启动！"
        ;;
    3)
        echo "停止服务..."
        cd docker && docker-compose down 2>/dev/null
        echo "服务已停止"
        ;;
    4)
        echo "重启服务..."
        cd docker || exit 1
        if ! docker-compose restart; then
            echo "重启失败！" >&2
            cd ..
            exit 1
        fi
        cd ..
        echo "服务已重启"
        ;;
    5)
        echo "查看日志（按 Ctrl+C 退出）..."
        cd docker && docker-compose logs -f
        ;;
    6)
        echo "清理并重新部署..."
        cd docker || exit 1
        docker-compose down -v 2>/dev/null
        if ! docker-compose build --no-cache; then
            echo "构建失败！" >&2
            cd ..
            exit 1
        fi
        if ! docker-compose up -d; then
            echo "启动失败！" >&2
            cd ..
            exit 1
        fi
        cd ..
        echo "服务已重新部署！"
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "完成！"

