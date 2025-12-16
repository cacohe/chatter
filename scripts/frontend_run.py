"""
前端服务启动脚本

使用方法:
    python frontend_run.py                    # 使用默认配置
    python frontend_run.py --port 8502         # 指定端口
    python frontend_run.py --server.address 0.0.0.0  # 指定监听地址
    python frontend_run.py --server.headless true    # 无浏览器模式
"""
import sys
import subprocess
from pathlib import Path

from src.infra.log.logger import logger


def main():
    """使用 streamlit run 命令启动前端服务"""
    # 获取项目根目录（脚本在 scripts/ 目录下，需要向上一级）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 获取前端主文件路径（从项目根目录）
    frontend_main = project_root / "src" / "frontend" / "main.py"
    
    # 验证文件是否存在
    if not frontend_main.exists():
        logger.error(f"错误: 找不到文件 {frontend_main}", file=sys.stderr)
        logger.error(f"当前工作目录: {Path.cwd()}", file=sys.stderr)
        logger.error(f"项目根目录: {project_root}", file=sys.stderr)
        sys.exit(1)
    
    # 切换到项目根目录（确保相对导入正常工作）
    import os
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # 构建 streamlit run 命令（使用绝对路径更可靠）
        cmd = ["streamlit", "run", str(frontend_main.resolve())]
        
        # 添加命令行参数
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        # 使用 subprocess 运行 streamlit
        subprocess.run(cmd, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        logger.error("\n服务已停止")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        logger.error(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        logger.error("错误: 未找到 streamlit 命令，请确保已安装 streamlit", file=sys.stderr)
        sys.exit(1)
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
