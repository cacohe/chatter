import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    frontend_root = Path(__file__).resolve().parent
    app = frontend_root / "src" / "main.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(frontend_root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )

    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "run", "streamlit", "run", str(app), *sys.argv[1:]]
    else:
        streamlit_path = shutil.which("streamlit")
        if not streamlit_path:
            print(
                "未找到 uv 或 streamlit。请先执行: cd frontend && uv sync",
                file=sys.stderr,
            )
            raise SystemExit(1)
        cmd = [streamlit_path, "run", str(app), *sys.argv[1:]]

    raise SystemExit(
        subprocess.call(cmd, cwd=str(frontend_root), env=env, shell=(os.name == "nt"))
    )


if __name__ == "__main__":
    main()
