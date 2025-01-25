import logging
import os


def setup_logger(log_file_path: str) -> logging.Logger:
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
        ]
    )
    logger = logging.getLogger(__name__)
    return logger
