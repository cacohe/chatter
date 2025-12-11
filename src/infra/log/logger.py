import logging
import os
import socket

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

host_name = socket.gethostname()
formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t' + host_name +
                              '\t%(message)s\t[%(filename)s]\t[%(lineno)d]')

logs_path = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

file_handler = logging.FileHandler(os.path.join(logs_path, 'app.log'))
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

