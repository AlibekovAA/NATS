import json
import base64
from typing import BinaryIO, List, Literal, Dict, Any
import uuid

from app.backend.models import NetworkAnalysisResult
from app.backend.nats_client import NATSClient
from app.backend.log import get_logger

EncodingType = Literal["hex", "base64"]


class NetworkAnalyzer:
    def __init__(self, nats_client: NATSClient) -> None:
        self.nats_client = nats_client
        self.chunk_size = 256 * 1024
        self.default_encoding: EncodingType = "hex"
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

    async def analyze_pcap(self, file: BinaryIO, encoding: EncodingType = "hex") -> NetworkAnalysisResult:
        max_payload = self.nats_client.client.max_payload
        analysis_id = str(uuid.uuid4())
        self.logger.info(f"[Analysis] Starting new analysis (ID: {analysis_id})")

        chunks = self._split_file(file)
        total_chunks = len(chunks)
        self.logger.info(f"[Analysis] File split into {total_chunks} chunks")

        await self.nats_client.publish(
            "network.analysis.start",
            json.dumps({
                "analysis_id": analysis_id,
                "total_chunks": total_chunks,
                "encoding": encoding
            }).encode()
        )

        for i, chunk in enumerate(chunks):
            chunk_data = self._encode_chunk(chunk, encoding)
            chunk_size = len(chunk_data)

            if chunk_size > max_payload:
                self.logger.error(f"[Analysis] Chunk {i} exceeds max payload ({chunk_size} > {max_payload} bytes)")
                raise Exception(f"Chunk {i} exceeds maximum size of {max_payload} bytes")

            response = await self.nats_client.request(
                "network.analysis.chunk",
                json.dumps({
                    "analysis_id": analysis_id,
                    "chunk_number": i,
                    "total_chunks": total_chunks,
                    "data": chunk_data,
                    "encoding": encoding
                }).encode(),
                timeout=30.0
            )

            response_data = self._decode_response(response.data, f"Chunk {i+1}/{total_chunks}")
            if "error" in response_data:
                self.logger.error(f"[Analysis] Error processing chunk {i}: {response_data['error']}")
                raise Exception(f"Error processing chunk {i}: {response_data['error']}")

            if response_data.get("status") != "ok":
                self.logger.error(f"[Analysis] Unexpected response for chunk {i}: {response_data}")
                raise Exception(f"Unexpected response for chunk {i}")

        self.logger.info("[Analysis] Requesting final analysis")
        final_response = await self.nats_client.request(
            "network.analysis.finish",
            json.dumps({
                "analysis_id": analysis_id,
                "encoding": encoding
            }).encode(),
            timeout=60.0
        )

        result_data = self._decode_response(final_response.data, "Final analysis")
        if "error" in result_data:
            self.logger.error(f"[Analysis] Analysis failed: {result_data['error']}")
            raise Exception(f"Analysis failed: {result_data['error']}")

        self.logger.info(f"[Analysis] Completed successfully. Processed {len(result_data.get('packets', []))} packets")
        return NetworkAnalysisResult(**result_data)

    def _split_file(self, file_pcap: BinaryIO) -> List[bytes]:
        chunks = []
        total_size = 0

        while True:
            chunk = file_pcap.read(self.chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
            total_size += len(chunk)

        self.logger.info(f"[Analysis] File split: {len(chunks)} chunks, {total_size} bytes total")
        return chunks
