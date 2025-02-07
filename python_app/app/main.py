from contextlib import asynccontextmanager
from io import BytesIO
from typing import Annotated, AsyncGenerator, cast

from fastapi import FastAPI, HTTPException, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator

from app.backend.log import get_logger
from app.backend.nats_client import NATSClient
from app.backend.models import NetworkAnalysisResult
from app.backend.config import NATS_SERVER_URL, MAX_FILE_SIZE
from app.backend.network_analyzer import NetworkAnalyzer
from app.backend.exception_handlers import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler
)


logger = get_logger(__name__)


class AppState:
    def __init__(self) -> None:
        self.nats_client: NATSClient = NATSClient(server_url=NATS_SERVER_URL)
        self.network_analyzer: NetworkAnalyzer = NetworkAnalyzer(self.nats_client)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    state = AppState()
    app.state.nats_client = state.nats_client
    app.state.network_analyzer = state.network_analyzer

    try:
        await app.state.nats_client.connect()
        logger.info("[Server] Python server started and connected to NATS")
        yield
    except Exception as e:
        logger.error(f"[Server] Failed to start server: {str(e)}")
        raise
    finally:
        await app.state.nats_client.close()
        logger.info("[Server] Python server shutting down")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

instrumentator = Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


def get_app_state() -> AppState:
    return cast(AppState, app.state)


async def get_analyzer() -> NetworkAnalyzer:
    return get_app_state().network_analyzer


@app.get("/", response_class=HTMLResponse)
async def get_html() -> HTMLResponse:
    with open("app/frontend/index.html") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check() -> dict[str, bool | str]:
    return {
        "status": "healthy",
        "nats_connected": app.state.nats_client.is_connected()
    }


@app.post("/analyze-network", response_model=NetworkAnalysisResult)
async def analyze_network_packets(
    file: UploadFile,
    analyzer: Annotated[NetworkAnalyzer, Depends(get_analyzer)]
) -> NetworkAnalysisResult:
    if not file.filename or not (file.filename.lower().endswith(('.pcap', '.pcapng'))):
        logger.warning(f"[API] Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PCAP/PCAPNG files are supported")

    pcap_buffer = BytesIO()
    size = 0

    content = await file.read()
    size = len(content)
    if size > MAX_FILE_SIZE:
        logger.warning(f"[API] File size exceeds limit: {size} bytes")
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        )
    pcap_buffer.write(content)

    pcap_buffer.seek(0)
    try:
        return await analyzer.analyze_pcap(pcap_buffer)
    except Exception as e:
        logger.error(f"[API] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
