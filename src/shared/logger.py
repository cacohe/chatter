import logging
import os
import socket
from pathlib import Path

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

host_name = socket.gethostname()
formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t' + host_name +
                              '\t%(message)s\t[%(filename)s]\t[%(lineno)d]')

base_path = Path(__file__).resolve().parent.parent.parent # 根据你的目录结构调整
logs_path = base_path / "logs"

if not logs_path.exists():
    logs_path.mkdir(parents=True, exist_ok=True)

file_handler = logging.FileHandler(os.path.join(logs_path, 'app.log'))
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

