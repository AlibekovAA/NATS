from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.backend.models.app_state import AppState
from app.backend.log import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    state = AppState()
    app.state.nats_client = state.nats_client
    app.state.network_analyzer = state.network_analyzer

    try:
        await app.state.nats_client.connect()
        logger.info("[Server] Python server started and connected to NATS")
        yield
    except Exception as e:
        logger.error(f"[Server] Failed to start server: {str(e)}")
        raise
    finally:
        await app.state.nats_client.close()
        logger.info("[Server] Python server shutting down")
