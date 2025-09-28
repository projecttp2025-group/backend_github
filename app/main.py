from fastapi import FastAPI
import uvicorn
from app.api.v1.router import api_router

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
    return {"service": "finance-assistant-backend", "version": "0.1.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)