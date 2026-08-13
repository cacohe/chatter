import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


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
    repo_root = Path(__file__).resolve().parent
    backend_root = repo_root / "backend"
    frontend_root = repo_root / "frontend"
    uv = shutil.which("uv")
    if not uv:
        print("未找到 uv。请先安装 uv。", file=sys.stderr)
        raise SystemExit(1)

    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = (
        str(backend_root / "src") + os.pathsep + backend_env.get("PYTHONPATH", "")
    )
    frontend_env = os.environ.copy()
    frontend_env["PYTHONPATH"] = (
        str(frontend_root / "src") + os.pathsep + frontend_env.get("PYTHONPATH", "")
    )

    processes: list[subprocess.Popen] = []
    try:
        print("正在启动后端服务...")
        backend = subprocess.Popen(
            [uv, "run", "python", "-m", "main"],
            cwd=str(backend_root),
            env=backend_env,
        )
        processes.append(backend)

        print("正在启动前端服务...")
        frontend = subprocess.Popen(
            [uv, "run", "streamlit", "run", str(frontend_root / "src" / "main.py")],
            cwd=str(frontend_root),
            env=frontend_env,
        )
        processes.append(frontend)

        print("前后端已启动，按 Ctrl+C 停止")
        while True:
            if backend.poll() is not None:
                print(f"后端进程退出，退出码: {backend.returncode}", file=sys.stderr)
                raise SystemExit(backend.returncode or 1)
            if frontend.poll() is not None:
                print(f"前端进程退出，退出码: {frontend.returncode}", file=sys.stderr)
                raise SystemExit(frontend.returncode or 1)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("用户请求停止服务")
    finally:
        _stop(processes)


if __name__ == "__main__":
    main()
