"""前端日志只打控制台，不写文件。"""

import logging
import socket

logger = logging.getLogger("frontend")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    host_name = socket.gethostname()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s\t%(levelname)s\t"
            + host_name
            + "\t%(message)s\t[%(filename)s]\t[%(lineno)d]"
        )
    )
    logger.addHandler(handler)
