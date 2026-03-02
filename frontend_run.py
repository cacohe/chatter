import sys
import os
import subprocess
import shutil
from pathlib import Path

from src.shared.logger import logger
from src.shared.utils import load_env


def main():
    """使用 streamlit run 命令启动前端服务"""
    load_env()
    # 1. 确定项目根目录
    # 无论从哪调用，以当前文件位置为基准向上推一级是最稳妥的
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir

    # 2. 获取前端主文件路径
    frontend_main = project_root / "src" / "frontend" / "main.py"

    # 3. 验证前端主文件是否存在
    if not frontend_main.exists():
        logger.error(f"找不到前端入口文件: {frontend_main}")
        logger.info(f"项目根目录探测为: {project_root}")
        sys.exit(1)

    # 4. 寻找 streamlit 执行路径 (解决 Windows 环境下的 FileNotFoundError)
    streamlit_path = shutil.which("streamlit")
    if not streamlit_path:
        logger.error("未找到 streamlit 命令。请确保已安装 streamlit 并在虚拟环境中运行。")
        sys.exit(1)

    # 5. 构建命令
    # 使用 streamlit_path 替代字符串 "streamlit" 更健壮
    cmd = [streamlit_path, "run", str(frontend_main.resolve())]

    # 透传剩余参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    logger.info(f"正在启动前端服务: {' '.join(cmd)}")

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
