import logging
import os
import pytz
from datetime import datetime


def setup_logger(log_file_path: str) -> logging.Logger:
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    moscow_tz = pytz.timezone('Europe/Moscow')

    class MoscowFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created)
            dt = pytz.utc.localize(dt).astimezone(moscow_tz)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    formatter = MoscowFormatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s"
    )

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger
