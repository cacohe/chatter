.PHONY: help install dev-up dev-down build up down logs logs-backend logs-frontend restart clean test

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make install      - 安装依赖"
	@echo "  make dev-up       - 启动开发环境（本地）"
	@echo "  make dev-down     - 停止开发环境"
	@echo "  make build        - 构建 Docker 镜像"
	@echo "  make up           - 启动 Docker 服务"
	@echo "  make down         - 停止 Docker 服务"
	@echo "  make logs         - 查看所有服务日志"
	@echo "  make logs-backend - 查看后端日志"
	@echo "  make logs-frontend - 查看前端日志"
	@echo "  make restart      - 重启服务"
	@echo "  make clean        - 清理 Docker 资源"
	@echo "  make test         - 运行测试"

# 安装依赖
install:
	pip install -r requirements.txt

# 开发环境启动
dev-up:
	@echo "启动开发环境..."
	@echo "后端服务: http://localhost:8000"
	@echo "前端服务: http://localhost:8501"
	python scripts/backend_run.py --reload &
	python scripts/frontend_run.py &

# 开发环境停止
dev-down:
	@pkill -f "backend_run.py" || true
	@pkill -f "frontend_run.py" || true
	@pkill -f "uvicorn" || true
	@pkill -f "streamlit" || true

# 构建 Docker 镜像
build:
	cd docker && docker-compose build

# 启动服务
up:
	cd docker && docker-compose up -d
	@echo "服务已启动:"
	@echo "  后端 API: http://localhost:8000"
	@echo "  前端界面: http://localhost:8501"
	@echo "  API文档: http://localhost:8000/docs"

# 停止服务
down:
	cd docker && docker-compose down

# 查看所有日志
logs:
	cd docker && docker-compose logs -f

# 查看后端日志
logs-backend:
	cd docker && docker-compose logs -f backend

# 查看前端日志
logs-frontend:
	cd docker && docker-compose logs -f frontend

# 重启服务
restart:
	cd docker && docker-compose restart

# 清理 Docker 资源
clean:
	cd docker && docker-compose down -v
	docker system prune -f

# 运行测试
test:
	pytest tests/ -v

# 格式化代码
format:
	black src/
	isort src/

# 代码检查
lint:
	flake8 src/
	mypy src/

