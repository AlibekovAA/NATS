import asyncio
from functools import wraps
from typing import Callable, Awaitable, Dict, Optional, Any
import time

from nats.aio.client import Client as NATS, Msg
from nats.aio.subscription import Subscription
from prometheus_client import Counter, Histogram

from app.backend.log import get_logger

logger = get_logger(__name__)

NATS_PUBLISH_COUNTER = Counter('nats_publish_total', 'Количество публикаций NATS', ['status'])
NATS_REQUEST_COUNTER = Counter('nats_request_total', 'Количество запросов NATS', ['status'])
NATS_REQUEST_LATENCY = Histogram('nats_request_latency_seconds', 'Время ответа NATS')


def retry_connection(retries: int = 3, delay: float = 1.0) -> Callable:
    def decorator(func: Callable[..., Awaitable[Optional[Any]]]) -> Callable[..., Awaitable[Optional[Any]]]:
        @wraps(func)
        async def wrapper(self: "NATSClient", *args: Any, **kwargs: Any) -> Optional[Any]:
            for attempt in range(retries):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator


class NATSClient:
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.client = NATS()
        self._connected = False
        self._subscribers: Dict[str, Subscription] = {}
        self._connection_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None

    @retry_connection(retries=3)
    async def connect(self) -> None:
        async with self._connection_lock:
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
                self._start_reconnect_monitor()
            except Exception as e:
                logger.error(f"[NATS] Connection failed: {str(e)}")
                raise

    def _start_reconnect_monitor(self) -> None:
        async def monitor() -> None:
            while True:
                if not self.is_connected() and self._connected:
                    logger.warning("[NATS] Connection lost, attempting to reconnect")
                    try:
                        await self.connect()
                    except Exception as e:
                        logger.error(f"[NATS] Reconnection failed: {str(e)}")
                await asyncio.sleep(5)

        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(monitor())

    async def subscribe(self, subject: str, callback: Callable[[Msg], Awaitable[None]]) -> Subscription:
        if subject not in self._subscribers:
            sub = await self.client.subscribe(subject, cb=callback)
            self._subscribers[subject] = sub
            return sub
        return self._subscribers[subject]

    async def request(self, subject: str, payload: bytes, timeout: float = 30.0) -> Msg:
        if not self.is_connected():
            await self.connect()
        start_time = time.monotonic()
        try:
            result = await self.client.request(subject, payload, timeout=timeout)
            NATS_REQUEST_COUNTER.labels(status='success').inc()
            NATS_REQUEST_LATENCY.observe(time.monotonic() - start_time)
            return result
        except Exception as e:
            NATS_REQUEST_COUNTER.labels(status='error').inc()
            NATS_REQUEST_LATENCY.observe(time.monotonic() - start_time)
            raise

    async def close(self) -> None:
        if self.client is None or not self.is_connected():
            logger.info("[NATS] No active connection to close")
            return
        try:
            await self.client.close()
            self._connected = False
            logger.info("[NATS] Connection closed")
        except Exception as e:
            logger.error(f"[NATS] Error closing NATS connection: {str(e)}")
            raise

    def is_connected(self) -> bool:
        return self._connected and self.client is not None and self.client.is_connected

    class NATSConnectionError(Exception):
        pass

    async def publish(self, subject: str, message: bytes) -> None:
        try:
            if not self.is_connected():
                raise self.NATSConnectionError("NATS client is not connected")
            await self.client.publish(subject, message)
            NATS_PUBLISH_COUNTER.labels(status='success').inc()
        except Exception as e:
            NATS_PUBLISH_COUNTER.labels(status='error').inc()
            raise self.NATSConnectionError(f"Failed to publish message: {str(e)}")
