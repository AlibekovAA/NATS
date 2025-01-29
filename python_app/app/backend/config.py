import os

NATS_SERVER_URL = os.getenv("NATS_SERVER_URL", "nats://nats:4222")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")
