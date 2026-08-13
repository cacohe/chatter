import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    backend_root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(backend_root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )

    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "run", "python", "-m", "main", *sys.argv[1:]]
    else:
        cmd = [sys.executable, "-m", "main", *sys.argv[1:]]

    raise SystemExit(
        subprocess.call(cmd, cwd=str(backend_root), env=env, shell=(os.name == "nt"))
    )


if __name__ == "__main__":
    main()
