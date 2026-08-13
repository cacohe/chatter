from pathlib import Path

from dotenv import load_dotenv


def load_env(env_path=None) -> None:
    """加载本地环境文件；已存在的环境变量优先（不覆盖）。

    查找顺序（显式路径除外）：
    1. backend/.env.local、backend/.env
    2. 仓库根目录 .env.local、.env
    """
    if env_path:
        path = Path(env_path)
        if path.exists():
            load_dotenv(dotenv_path=path, override=False)
        return

    backend_root = Path(__file__).resolve().parents[2]
    repo_root = backend_root.parent
    for base in (backend_root, repo_root):
        for name in (".env.local", ".env"):
            path = base / name
            if path.exists():
                load_dotenv(dotenv_path=path, override=False)
                return
