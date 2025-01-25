from fastapi import FastAPI
from backend.logger import setup_logger
from backend.nats_client import NATSClient

app = FastAPI()

log_file_path = "python_app/logs/app.log"
logger = setup_logger(log_file_path)

nats_client = NATSClient(server_url="nats://nats:4222")


@app.on_event("startup")
async def startup():
    await nats_client.connect()
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
