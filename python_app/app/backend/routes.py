from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, Depends
from fastapi.responses import HTMLResponse

from app.backend.models.analysis import NetworkAnalysisResult
from app.backend.network_analyzer import NetworkAnalyzer
from app.backend.config import MAX_FILE_SIZE
from app.backend.log import get_logger
from app.backend.dependencies import get_analyzer

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_html() -> HTMLResponse:
    with open("app/frontend/index.html") as f:
        return HTMLResponse(content=f.read())


@router.get("/health")
async def health_check() -> dict[str, bool | str]:
    return {
        "status": "healthy",
        "nats_connected": True
    }


@router.post("/analyze-network", response_model=NetworkAnalysisResult)
async def analyze_network_packets(
    file: UploadFile,
    analyzer: Annotated[NetworkAnalyzer, Depends(get_analyzer)]
) -> NetworkAnalysisResult:
    if not file.filename or not (file.filename.lower().endswith(('.pcap', '.pcapng'))):
        logger.warning(f"[API] Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PCAP/PCAPNG files are supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"[API] File size exceeds limit: {len(content)} bytes")
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        )

    pcap_buffer = BytesIO(content)
    try:
        return await analyzer.analyze_pcap(pcap_buffer)
    except Exception as e:
        logger.error(f"[API] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
