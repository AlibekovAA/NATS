from nats.aio.client import Client as NATS


class NATSClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = NATS()
        self._connected = False

    async def connect(self):
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

    async def close(self):
        await self.client.close()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self.client.is_connected

    class NATSConnectionError(Exception):
        pass

    async def publish(self, subject: str, message: bytes):
        try:
            if not self.is_connected():
                raise self.NATSConnectionError("NATS client is not connected")
            await self.client.publish(subject, message)
        except Exception as e:
            raise self.NATSConnectionError(f"Failed to publish message: {str(e)}")
