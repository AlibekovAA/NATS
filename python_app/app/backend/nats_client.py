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
        if self._connected:
            return

        try:
            await self.client.connect(
                self.server_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=5,
                ping_interval=20,
                allow_reconnect=True,
                connect_timeout=3
            )
            self._connected = True
            logger.info(f"[NATS] Connected to {self.server_url}")
        except Exception as e:
            logger.error(f"[NATS] Connection failed: {str(e)}")
            raise

    async def subscribe(self, subject: str, callback: Callable[[Msg], Awaitable[None]]) -> Subscription:
        if not self.is_connected():
            await self.connect()

        if subject not in self._subscribers:
            sub = await self.client.subscribe(subject, cb=callback)
            self._subscribers[subject] = sub
            return sub
        return self._subscribers[subject]

    async def publish(self, subject: str, message: bytes) -> None:
        if not self.is_connected():
            await self.connect()

        try:
            await self.client.publish(subject, message)
        except Exception as e:
            logger.error(f"[NATS] Failed to publish message: {str(e)}")
            raise

    async def request(self, subject: str, payload: bytes, timeout: float = 30.0) -> Msg:
        if not self.is_connected():
            await self.connect()

        try:
            return await self.client.request(subject, payload, timeout=timeout)
        except Exception as e:
            logger.error(f"[NATS] Request failed: {str(e)}")
            raise

    async def close(self) -> None:
        if self.is_connected():
            await self.client.close()
            self._connected = False
            logger.info("[NATS] Connection closed")

    def is_connected(self) -> bool:
        return self._connected and self.client is not None and self.client.is_connected
