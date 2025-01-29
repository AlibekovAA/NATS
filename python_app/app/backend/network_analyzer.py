import json
from typing import BinaryIO

from app.backend.models import NetworkAnalysisResult
from app.backend.nats_client import NATSClient


class NetworkAnalyzer:
    def __init__(self, nats_client: NATSClient) -> None:
        self.nats_client = nats_client

    async def analyze_pcap(self, file: BinaryIO) -> NetworkAnalysisResult:
        file_content = file.read()

        response = await self.nats_client.request(
            "network.analysis.task",
            file_content,
            timeout=30.0
        )

        result_data = json.loads(response.data.decode())
        return NetworkAnalysisResult(**result_data)
