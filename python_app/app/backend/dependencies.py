from typing import cast, Optional

from fastapi import FastAPI

from app.backend.models.app_state import AppState
from app.backend.network_analyzer import NetworkAnalyzer


def get_app_state() -> AppState:
    if app is None:
        raise RuntimeError("FastAPI application is not initialized")
    return cast(AppState, app.state)


async def get_analyzer() -> NetworkAnalyzer:
    return get_app_state().network_analyzer


app: Optional[FastAPI] = None


def init_app(application: FastAPI) -> None:
    global app
    app = application
