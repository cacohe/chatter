import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from src.shared.logger import logger
from src.shared.utils import load_env


def _build_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _stop(processes: list[subprocess.Popen]) -> None:
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> None:
    load_env()
    project_root = Path(__file__).resolve().parent
    backend_main = project_root / "src" / "backend" / "main.py"
    frontend_main = project_root / "src" / "frontend" / "main.py"

    if not backend_main.exists():
        logger.error(f"找不到后端入口文件: {backend_main}")
        sys.exit(1)
    if not frontend_main.exists():
        logger.error(f"找不到前端入口文件: {frontend_main}")
        sys.exit(1)

    streamlit_path = shutil.which("streamlit")
    if not streamlit_path:
        logger.error(
            "未找到 streamlit 命令。请确保已安装 streamlit 并在虚拟环境中运行。"
        )
        sys.exit(1)

    env = _build_env(project_root)
    processes: list[subprocess.Popen] = []

    try:
        logger.info("正在启动后端服务...")
        backend = subprocess.Popen(
            [sys.executable, str(backend_main)],
            cwd=str(project_root),
            env=env,
        )
        processes.append(backend)

        logger.info("正在启动前端服务...")
        frontend = subprocess.Popen(
            [streamlit_path, "run", str(frontend_main)],
            cwd=str(project_root),
            env=env,
        )
        processes.append(frontend)

        logger.info("前后端已启动，按 Ctrl+C 停止")
        while True:
            if backend.poll() is not None:
                logger.error(f"后端进程退出，退出码: {backend.returncode}")
                sys.exit(backend.returncode or 1)
            if frontend.poll() is not None:
                logger.error(f"前端进程退出，退出码: {frontend.returncode}")
                sys.exit(frontend.returncode or 1)
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("用户请求停止服务 (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"启动过程中发生未知错误: {e}")
        sys.exit(1)
    finally:
        _stop(processes)


if __name__ == "__main__":
    main()
