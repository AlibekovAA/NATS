import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    logger.propagate = False

    moscow_tz = pytz.timezone('Europe/Moscow')

    class MoscowTimeFormatter(logging.Formatter):
        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
            dt = datetime.fromtimestamp(record.created, tz=moscow_tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    formatter = MoscowTimeFormatter('[%(asctime)s] [%(levelname)s] %(message)s')

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
