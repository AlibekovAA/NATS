from fastapi import FastAPI, HTTPException
from backend.log import setup_logger
from backend.nats_client import NATSClient
from backend.models import Message
from backend.config import NATS_SERVER_URL, LOG_FILE_PATH

app = FastAPI()

logger = setup_logger(LOG_FILE_PATH)
nats_client = NATSClient(server_url=NATS_SERVER_URL)


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


@app.post("/send-message")
async def send_message(msg: Message):
    try:
        message_bytes = msg.message.encode("utf-8")
        await nats_client.publish("Data", message_bytes)
        logger.info(f"Message sent to NATS: {msg.message}")
        return {"message": "Message sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")
