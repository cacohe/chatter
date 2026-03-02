import sys
from pathlib import Path

from dotenv import load_dotenv

from src.shared.logger import logger


def load_env(env_path=None):
    if not env_path:
        env_path = Path(__file__).parent.parent.parent.resolve() / ".env.local"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"No environment variables file found at {env_path}")
        # sys.exit(1)
