from nats.aio.client import Client as NATS


class NATSClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = NATS()

    async def connect(self):
        await self.client.connect(self.server_url)

    async def close(self):
        await self.client.close()

    async def publish(self, subject: str, message: bytes):
        await self.client.publish(subject, message)
