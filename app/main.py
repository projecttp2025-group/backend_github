import logging

import uvicorn
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Finance Assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["root"])
def root():
    logger.debug("Root endpoint activated")
    return {"service": "finance-assistant-backend", "version": "0.1.0"}


if __name__ == "__main__":
    logger.info("App is started")
    uvicorn.run("app.main:app", reload=True)
