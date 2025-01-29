from typing import Callable, Awaitable, Dict
from nats.aio.client import Client as NATS, Msg
from nats.aio.subscription import Subscription


class NATSClient:
    def __init__(self, server_url: str) -> None:
        self.server_url: str = server_url
        self.client: NATS = NATS()
        self._connected: bool = False
        self._subscribers: Dict[str, Subscription] = {}

    async def connect(self) -> None:
        try:
            await self.client.connect(
                self.server_url,
                max_reconnect_attempts=5,
                reconnect_time_wait=2,
                ping_interval=20,
                max_outstanding_pings=5,
            )
            self._connected = True
        except Exception as e:
            self._connected = False
            raise

    async def subscribe(self, subject: str, callback: Callable[[Msg], Awaitable[None]]) -> Subscription:
        if subject not in self._subscribers:
            sub = await self.client.subscribe(subject, cb=callback)
            self._subscribers[subject] = sub
            return sub
        return self._subscribers[subject]

    async def request(self, subject: str, payload: bytes, timeout: float = 10.0) -> Msg:
        if not self.is_connected():
            raise self.NATSConnectionError("NATS client is not connected")
        return await self.client.request(subject, payload, timeout=timeout)

    async def close(self) -> None:
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
