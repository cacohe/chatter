import logging
import socket
from pathlib import Path

from src.shared.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_settings.log_level.upper(), logging.INFO))

host_name = socket.gethostname()
formatter = logging.Formatter(
    "%(asctime)s\t%(levelname)s\t"
    + host_name
    + "\t%(message)s\t[%(filename)s]\t[%(lineno)d]"
)

log_dir = Path(settings.log_settings.log_path)
if not log_dir.is_absolute():
    log_dir = Path(__file__).resolve().parent.parent.parent / log_dir
log_dir.mkdir(parents=True, exist_ok=True)

if not logger.handlers:
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
