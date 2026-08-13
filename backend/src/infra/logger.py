"""进程日志：同时写控制台与 backend/logs/app.log。"""

import logging
import socket
from pathlib import Path

from infra.config import settings

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
    # 相对路径锚定到 backend/ 根目录，避免随启动 cwd 漂移
    log_dir = Path(__file__).resolve().parents[2] / log_dir
log_dir.mkdir(parents=True, exist_ok=True)

if not logger.handlers:
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
