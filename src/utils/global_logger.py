# Configure logger

import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_logging_handler = logging.StreamHandler()
console_logging_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
console_logging_handler.setLevel(logging.DEBUG)
logger.addHandler(console_logging_handler)

# 创建日志目录（如果不存在）
log_directory = "log"
os.makedirs(log_directory, exist_ok=True)  # 如果目录不存在，则创建它

# 获取当前日期作为日志文件名的一部分
current_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
log_file_name = f"{current_date}.log"

# 配置文件日志处理器
file_logging_handler = logging.FileHandler(os.path.join(log_directory, log_file_name))
file_logging_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
file_logging_handler.setLevel(logging.DEBUG)
logger.addHandler(file_logging_handler)
