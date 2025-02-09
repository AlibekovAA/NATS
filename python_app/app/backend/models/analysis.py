from dataclasses import dataclass
from typing import Optional, List, Literal
from pydantic import BaseModel


class NetworkPacket(BaseModel):
    source_ip: str
    destination_ip: str
    protocol: str
    size: int
    timestamp: str
    additional_info: Optional[dict] = None


class NetworkAnalysisResult(BaseModel):
    packets: List[NetworkPacket]
    summary: dict


@dataclass
class ChunkInfo:
    number: int
    data: bytes
    total_chunks: int
    encoding: Literal["hex", "base64"]


class AnalysisMessage(BaseModel):
    analysis_id: str
    chunk_number: Optional[int] = None
    total_chunks: int
    data: Optional[str] = None
    encoding: Literal["hex", "base64"]
