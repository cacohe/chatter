import os
import subprocess
import sys
from pathlib import Path

from src.shared.logger import logger
from src.shared.utils import load_env


def main():
    # 1. 确定项目根目录
    # 无论从哪调用，以当前文件位置为基准向上推一级是最稳妥的
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # 2. 获取前端主文件路径
    frontend_main = project_root / "src" / "backend" / "main.py"

    # 3. 验证前端主文件是否存在
    if not frontend_main.exists():
        logger.error(f"找不到前端入口文件: {frontend_main}")
        logger.info(f"项目根目录探测为: {project_root}")
        sys.exit(1)

    cmd = ['python', str(frontend_main.resolve())]

    # 透传剩余参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    logger.info(f"正在启动后端服务: {' '.join(cmd)}")

    env = os.environ.copy()
    # 将当前项目根目录加入 PYTHONPATH
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        # 6. 核心：运行子进程
        # shell=True 在 Windows 上能更好地解析 PATH 里的脚本
        # env=os.environ 确保环境变量透传
        subprocess.run(
            cmd,
            check=True,
            cwd=str(project_root),
            env=env,
            shell=(os.name == 'nt')  # 仅在 Windows 上开启 shell 模式
        )
    except KeyboardInterrupt:
        logger.info("用户请求停止服务 (KeyboardInterrupt)")
    except subprocess.CalledProcessError as e:
        logger.error(f"Streamlit 进程异常退出: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动过程中发生未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
