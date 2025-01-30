import json
from typing import BinaryIO, List
import uuid
import base64

from app.backend.models import NetworkAnalysisResult
from app.backend.nats_client import NATSClient


class NetworkAnalyzer:
    def __init__(self, nats_client: NATSClient) -> None:
        self.nats_client = nats_client
        self.chunk_size = 256 * 1024

    async def analyze_pcap(self, file: BinaryIO) -> NetworkAnalysisResult:
        max_payload = self.nats_client.client.max_payload

        analysis_id = str(uuid.uuid4())
        chunks = self._split_file(file)
        total_chunks = len(chunks)

        await self.nats_client.publish(
            "network.analysis.start",
            json.dumps({
                "analysis_id": analysis_id,
                "total_chunks": total_chunks
            }).encode()
        )

        for i, chunk in enumerate(chunks):
            chunk_data = base64.b64encode(chunk).decode('ascii')
            if len(chunk_data) > max_payload:
                raise Exception(f"Размер чанка {i} превышает максимально допустимый размер {max_payload} байт")

            response = await self.nats_client.request(
                "network.analysis.chunk",
                json.dumps({
                    "analysis_id": analysis_id,
                    "chunk_number": i,
                    "total_chunks": total_chunks,
                    "data": chunk_data,
                    "encoding": "base64"
                }).encode(),
                timeout=30.0
            )

            response_data = json.loads(response.data.decode())
            if "error" in response_data:
                raise Exception(f"Ошибка при обработке чанка {i}: {response_data['error']}")
            if response_data.get("status") != "ok":
                raise Exception(f"Неожиданный ответ при обработке чанка {i}")

        final_response = await self.nats_client.request(
            "network.analysis.finish",
            json.dumps({"analysis_id": analysis_id}).encode(),
            timeout=60.0
        )

        result_data = json.loads(final_response.data.decode())
        return NetworkAnalysisResult(**result_data)

    def _split_file(self, file_pcap: BinaryIO) -> List[bytes]:
        chunks = []
        while True:
            chunk = file_pcap.read(self.chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        return chunks
