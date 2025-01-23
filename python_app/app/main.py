import logging
from fastapi import FastAPI
from nats.aio.client import Client as NATS

app = FastAPI()
nats_client = NATS()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("python_app/logs/app.log"),
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
    return {"message": "Hello from Python App"}
