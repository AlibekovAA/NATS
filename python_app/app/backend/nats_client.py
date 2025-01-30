from typing import Callable, Awaitable, Dict
import asyncio
from nats.aio.client import Client as NATS, Msg
from nats.aio.subscription import Subscription
from nats.errors import NoServersError, TimeoutError, Error as NatsError


class NATSClient:
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.client = NATS()
        self._connected = False
        self._subscribers: Dict[str, Subscription] = {}

    async def connect(self, max_retries: int = 5, retry_interval: float = 2.0) -> None:
        retries = 0
        last_error = None

        while retries < max_retries:
            try:
                await self.client.connect(
                    servers=[self.server_url],
                    reconnect_time_wait=2,
                    max_reconnect_attempts=5,
                    connect_timeout=5
                )
                self._connected = True
                return
            except (NoServersError, TimeoutError, NatsError) as e:
                last_error = e
                retries += 1
                if retries < max_retries:
                    await asyncio.sleep(retry_interval)
                continue

        raise last_error or NoServersError("Failed to connect to NATS server")

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
        if self.client and self.client.is_connected:
            await self.client.close()
            self._connected = False

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
