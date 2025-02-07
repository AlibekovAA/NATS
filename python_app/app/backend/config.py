import os
from typing import Literal

NATS_SERVER_URL = "nats://nats:4222"
HOST = "localhost"
PORT = 8000
METRICS_ENDPOINT = f"http://{HOST}:{PORT}/metrics"
CHUNK_SIZE = 256 * 1024
DEFAULT_ENCODING: Literal["hex", "base64"] = "hex"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")
MAX_FILE_SIZE = 1024 * 1024 * 1024
