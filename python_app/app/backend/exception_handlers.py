from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from app.backend.log import get_logger

logger = get_logger(__name__)


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RequestValidationError):
        status_code = 422
        error_type = "Validation Error"
        detail = exc.errors()
        logger.warning(f"[API] Validation error: {exc}")
    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_type = "HTTP Error"
        detail = exc.detail
        logger.warning(f"[API] HTTP error {exc.status_code}: {exc.detail}")
    else:
        status_code = 500
        error_type = "Internal Server Error"
        detail = str(exc)
        logger.error(f"[API] Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "detail": detail,
            "path": str(request.url)
        }
    )
