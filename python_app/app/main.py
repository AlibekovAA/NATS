from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.backend.routes import router
from app.backend.lifespan import lifespan
from app.backend.dependencies import init_app
from app.backend.exception_handlers import error_handler


app = FastAPI(lifespan=lifespan)
init_app(app)

app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

app.add_exception_handler(Exception, error_handler)
app.add_exception_handler(RequestValidationError, error_handler)

app.include_router(router)
