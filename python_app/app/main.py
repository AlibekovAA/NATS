from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.backend.log import setup_logger
from app.backend.nats_client import NATSClient
from app.backend.models import Message
from app.backend.config import NATS_SERVER_URL, LOG_FILE_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    await nats_client.connect()
    logger.info("Python server started and connected to NATS")
    yield
    await nats_client.close()
    logger.info("Python server shutting down")

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/frontend/public"), name="static")

logger = setup_logger(LOG_FILE_PATH)
nats_client = NATSClient(server_url=NATS_SERVER_URL)


@app.get("/", response_class=HTMLResponse)
async def get_html():
    with open("app/frontend/public/index.html") as f:
        return HTMLResponse(content=f.read())


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


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "nats_connected": nats_client.is_connected()
    }
