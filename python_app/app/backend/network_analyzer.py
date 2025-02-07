import json
import base64
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import BinaryIO, List, Literal, Dict, Any
import asyncio
import time

from nats.aio.client import Msg
from prometheus_client import Counter, Histogram

from app.backend.models import NetworkAnalysisResult
from app.backend.nats_client import NATSClient
from app.backend.log import get_logger
from app.backend.config import CHUNK_SIZE, DEFAULT_ENCODING

EncodingType = Literal["hex", "base64"]

CHUNK_PROCESSED_COUNTER = Counter('chunk_processed_total', 'Количество обработанных чанков', ['status'])
CHUNK_PROCESSING_DURATION = Histogram('chunk_processing_duration_seconds', 'Продолжительность обработки одного чанка')
PCAP_ANALYSIS_DURATION_SECONDS = Histogram('pcap_analysis_duration_seconds', 'Время анализа pcap файла')


@dataclass
class ChunkInfo:
    number: int
    data: bytes
    total_chunks: int
    encoding: EncodingType


class NetworkAnalyzer:
    def __init__(self, nats_client: NATSClient) -> None:
        self.nats_client = nats_client
        self.chunk_size = CHUNK_SIZE
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._chunk_semaphore = asyncio.Semaphore(4)
        self.default_encoding: EncodingType = DEFAULT_ENCODING
        self.logger = get_logger(__name__)

    def _encode_chunk(self, chunk: bytes, encoding: EncodingType) -> str:
        if encoding == "hex":
            return chunk.hex()
        elif encoding == "base64":
            return base64.b64encode(chunk).decode('utf-8')

    def _decode_response(self, response_data: bytes, context: str = "") -> Dict[str, Any]:
        try:
            decoded: Dict[str, Any] = json.loads(response_data.decode('utf-8', errors='strict'))
            return decoded
        except UnicodeDecodeError as e:
            self.logger.error(f"[Analysis] {context}: Failed to decode response: {str(e)}")
            raise Exception("Failed to decode analyzer response") from e
        except json.JSONDecodeError as e:
            self.logger.error(f"[Analysis] {context}: Failed to parse JSON: {str(e)}")
            raise Exception("Failed to parse analyzer response") from e

    async def _process_chunk(
        self,
        chunk_info: ChunkInfo,
        analysis_id: str
    ) -> None:
        start_chunk = time.monotonic()
        try:
            async with self._chunk_semaphore:
                encoded_data = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self._encode_chunk(chunk_info.data, chunk_info.encoding)
                )
                response = await self.nats_client.request(
                    "network.analysis.chunk",
                    self._create_chunk_message(
                        analysis_id,
                        chunk_info.number,
                        chunk_info.total_chunks,
                        encoded_data,
                        chunk_info.encoding
                    ),
                    timeout=30.0
                )
                self._validate_response(response, f"Chunk {chunk_info.number + 1}")
            CHUNK_PROCESSED_COUNTER.labels(status='success').inc()
        except Exception as e:
            CHUNK_PROCESSED_COUNTER.labels(status='error').inc()
            raise
        finally:
            CHUNK_PROCESSING_DURATION.observe(time.monotonic() - start_chunk)

    def _create_chunk_message(
        self,
        analysis_id: str,
        chunk_number: int,
        total_chunks: int,
        data: str,
        encoding: str
    ) -> bytes:
        return json.dumps({
            "analysis_id": analysis_id,
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
            "data": data,
            "encoding": encoding
        }).encode()

    async def analyze_pcap(self, file: BinaryIO, encoding: EncodingType = "hex") -> NetworkAnalysisResult:
        analysis_id = str(uuid.uuid4())
        start_time = time.monotonic()
        try:
            chunks = self._split_file(file)
            total_chunks = len(chunks)
            self.logger.info(f"[Analysis] Starting analysis {analysis_id} with {total_chunks} chunks")
            await self.nats_client.publish(
                "network.analysis.start",
                self._create_start_message(analysis_id, total_chunks, encoding)
            )
            chunk_tasks = [
                self._process_chunk(
                    ChunkInfo(i, chunk, total_chunks, encoding),
                    analysis_id
                )
                for i, chunk in enumerate(chunks)
            ]
            await asyncio.gather(*chunk_tasks)
            final_response = await self.nats_client.request(
                "network.analysis.finish",
                self._create_finish_message(analysis_id),
                timeout=60.0
            )
            result = NetworkAnalysisResult(**self._decode_response(final_response.data))
            return result
        finally:
            PCAP_ANALYSIS_DURATION_SECONDS.observe(time.monotonic() - start_time)

    def _split_file(self, file_pcap: BinaryIO) -> List[bytes]:
        file_content = file_pcap.read()
        if len(file_content) < 4 or not (
            file_content.startswith(b'\xa1\xb2\xc3\xd4') or
            file_content.startswith(b'\xd4\xc3\xb2\xa1')
        ):
            raise ValueError("Invalid PCAP file format")
        chunks = []
        chunk_size = self.chunk_size
        first_chunk = file_content[:chunk_size]
        chunks.append(first_chunk)
        for i in range(chunk_size, len(file_content), chunk_size):
            chunk = file_content[i:i + chunk_size]
            chunks.append(chunk)
        self.logger.info(f"[Analysis] File split: {len(chunks)} chunks, {len(file_content)} bytes total")
        return chunks

    def _create_start_message(self, analysis_id: str, total_chunks: int, encoding: str) -> bytes:
        return json.dumps({
            "analysis_id": analysis_id,
            "total_chunks": total_chunks,
            "encoding": encoding
        }).encode()

    def _create_finish_message(self, analysis_id: str) -> bytes:
        return json.dumps({
            "analysis_id": analysis_id,
            "encoding": self.default_encoding
        }).encode()

    def _validate_response(self, response: Msg, context: str) -> None:
        response_data = self._decode_response(response.data, context)
        if "error" in response_data:
            self.logger.error(f"[Analysis] Error processing {context}: {response_data['error']}")
            raise Exception(f"Error processing {context}: {response_data['error']}")
        if response_data.get("status") != "ok":
            self.logger.error(f"[Analysis] Unexpected response for {context}: {response_data}")
            raise Exception(f"Unexpected response for {context}")
