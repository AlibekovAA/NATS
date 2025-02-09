import json
import base64
import uuid
from typing import BinaryIO, List
import asyncio

from app.backend.models.analysis import NetworkAnalysisResult, ChunkInfo, AnalysisMessage
from app.backend.nats_client import NATSClient
from app.backend.log import get_logger
from app.backend.config import CHUNK_SIZE, DEFAULT_ENCODING


logger = get_logger(__name__)


class NetworkAnalyzer:
    def __init__(self, nats_client: NATSClient) -> None:
        self.nats_client = nats_client
        self.chunk_size = CHUNK_SIZE
        self._chunk_semaphore = asyncio.Semaphore(4)

    def _encode_chunk(self, chunk: bytes) -> str:
        return chunk.hex() if DEFAULT_ENCODING == "hex" else base64.b64encode(chunk).decode('utf-8')

    async def _process_chunk(self, chunk_info: ChunkInfo, analysis_id: str) -> None:
        async with self._chunk_semaphore:
            msg = AnalysisMessage(
                analysis_id=analysis_id,
                chunk_number=chunk_info.number,
                total_chunks=chunk_info.total_chunks,
                data=self._encode_chunk(chunk_info.data),
                encoding=DEFAULT_ENCODING
            )

            response = await self.nats_client.request(
                "network.analysis.chunk",
                msg.model_dump_json().encode(),
                timeout=30.0
            )

            if error := json.loads(response.data).get("error"):
                raise Exception(f"Error processing chunk {chunk_info.number}: {error}")

    async def analyze_pcap(self, pcap_file: BinaryIO) -> NetworkAnalysisResult:
        analysis_id = str(uuid.uuid4())
        chunks = self._split_pcap(pcap_file)
        total_chunks = len(chunks)

        logger.info(f"[Analysis] Starting analysis {analysis_id} with {total_chunks} chunks")

        start_msg = AnalysisMessage(analysis_id=analysis_id, total_chunks=total_chunks, encoding=DEFAULT_ENCODING)
        await self.nats_client.publish("network.analysis.start", start_msg.model_dump_json().encode())

        chunk_tasks = [
            self._process_chunk(ChunkInfo(i, chunk, total_chunks, DEFAULT_ENCODING), analysis_id)
            for i, chunk in enumerate(chunks)
        ]
        await asyncio.gather(*chunk_tasks)

        finish_msg = AnalysisMessage(analysis_id=analysis_id, total_chunks=total_chunks, encoding=DEFAULT_ENCODING)
        final_response = await self.nats_client.request(
            "network.analysis.finish",
            finish_msg.model_dump_json().encode(),
            timeout=60.0
        )

        return NetworkAnalysisResult(**json.loads(final_response.data))

    def _split_pcap(self, pcap_file: BinaryIO) -> List[bytes]:
        content = pcap_file.read()
        if len(content) < 24:
            raise ValueError("Invalid PCAP file: too small")

        chunks = [content[i:i + self.chunk_size] for i in range(0, len(content), self.chunk_size)]
        logger.info(f"[Analysis] Split file into {len(chunks)} chunks")
        return chunks
