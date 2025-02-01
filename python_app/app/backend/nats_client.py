from typing import Callable, Awaitable, Dict

from nats.aio.client import Client as NATS, Msg
from nats.aio.subscription import Subscription

from app.backend.log import get_logger

logger = get_logger(__name__)


class NATSClient:
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.client = NATS()
        self._connected = False
        self._subscribers: Dict[str, Subscription] = {}

    async def connect(self) -> None:
        try:
            await self.client.connect(self.server_url)
            self._connected = True
            logger.info(f"[NATS] Connected to NATS server at {self.server_url}")
        except Exception as e:
            logger.error(f"[NATS] Failed to connect to NATS server: {str(e)}")
            raise

    async def subscribe(self, subject: str, callback: Callable[[Msg], Awaitable[None]]) -> Subscription:
        if subject not in self._subscribers:
            sub = await self.client.subscribe(subject, cb=callback)
            self._subscribers[subject] = sub
            return sub
        return self._subscribers[subject]

    async def request(self, subject: str, payload: bytes, timeout: float = 30.0) -> Msg:
        if not self.is_connected():
            raise RuntimeError("NATS client is not connected")
        return await self.client.request(subject, payload, timeout=timeout)

    async def close(self) -> None:
        try:
            await self.client.close()
            self._connected = False
            logger.info("[NATS] Connection closed")
        except Exception as e:
            logger.error(f"[NATS] Error closing NATS connection: {str(e)}")
            raise

    def is_connected(self) -> bool:
        return self._connected and self.client.is_connected

    class NATSConnectionError(Exception):
        pass

    async def publish(self, subject: str, message: bytes) -> None:
        try:
            if not self.is_connected():
                raise self.NATSConnectionError("NATS client is not connected")
            await self.client.publish(subject, message)
        except Exception as e:
            raise self.NATSConnectionError(f"Failed to publish message: {str(e)}")
