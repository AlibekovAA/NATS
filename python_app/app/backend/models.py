from pydantic import BaseModel
from typing import Optional, List


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


class TestModel(BaseModel):
    name: str
