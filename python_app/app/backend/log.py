import logging
from datetime import datetime
import pytz
import os


def setup_logger(log_file_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    moscow_tz = pytz.timezone('Europe/Moscow')

    class MoscowTimeFormatter(logging.Formatter):
        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
            dt = datetime.fromtimestamp(record.created, tz=moscow_tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)

    formatter = MoscowTimeFormatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
