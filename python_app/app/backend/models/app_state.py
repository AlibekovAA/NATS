from app.backend.nats_client import NATSClient
from app.backend.network_analyzer import NetworkAnalyzer
from app.backend.config import NATS_SERVER_URL


class AppState:
    def __init__(self) -> None:
        self.nats_client: NATSClient = NATSClient(server_url=NATS_SERVER_URL)
        self.network_analyzer: NetworkAnalyzer = NetworkAnalyzer(self.nats_client)
