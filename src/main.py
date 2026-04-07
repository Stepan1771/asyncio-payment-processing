from pathlib import Path

import uvicorn

from fastapi import FastAPI


from api import api_router
from core.config import app_settings
from core.lifespan import lifespan

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(
        title=app_settings.app.service_name,
        lifespan=lifespan
    )
    app.include_router(api_router, prefix=app_settings.api.prefix)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=app_settings.app.host,
        port=app_settings.app.port,
    )