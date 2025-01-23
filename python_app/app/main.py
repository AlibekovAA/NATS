import logging
import os

from fastapi import FastAPI
from nats.aio.client import Client as NATS

app = FastAPI()
nats_client = NATS()

log_file_path = "python_app/logs/app.log"
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


@app.on_event("startup")
async def startup():
    await nats_client.connect("nats://nats:4222")
    logger.info("Python server started and connected to NATS")


@app.on_event("shutdown")
async def shutdown():
    await nats_client.close()
    logger.info("Python server shutting down")


@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed")
    message_data = {"event": "User accessed root endpoint"}
    message_bytes = str(message_data).encode("utf-8")
    await nats_client.publish("Data", message_bytes)
    return {"message": "Hello from App"}
