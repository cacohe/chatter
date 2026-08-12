from pathlib import Path

from dotenv import load_dotenv


def load_env(env_path=None):
    if not env_path:
        env_path = Path(__file__).parent.parent.parent.resolve() / ".env.local"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
