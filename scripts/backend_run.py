"""
后端服务启动脚本

使用方法:
    python backend_run.py                    # 使用默认配置
    python backend_run.py --host 0.0.0.0     # 指定监听地址
    python backend_run.py --port 8080        # 指定端口
    python backend_run.py --reload           # 开发模式（自动重载）
    python backend_run.py --host 0.0.0.0 --port 8080 --reload

或者直接运行:
    python -m src.backend.main
"""
from pathlib import Path

from dotenv import load_dotenv

# 直接导入并运行，main 模块会处理命令行参数
from src.backend.main import main
from src.infra.log.logger import logger

from pathlib import Path

from dotenv import load_dotenv
# 加载 .env.local 文件（如果存在）
env_path = Path(__file__).parent.parent.resolve() / ".env.local"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"No environment variables file found at {env_path}")


if __name__ == "__main__":
    # 直接调用，main 函数在模块的 __main__ 块中已经处理了命令行参数
    # 但这里我们需要手动处理，因为直接调用 main() 不会解析 sys.argv
    import sys
    import argparse
    from src.config import settings
    
    parser = argparse.ArgumentParser(description="启动多模型AI聊天机器人后端服务")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"监听地址（默认: {settings.backend_host}）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"监听端口（默认: {settings.backend_port}）"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    
    args = parser.parse_args()
    
    try:
        main(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        logger.error("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)
