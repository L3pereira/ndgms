from fastapi import FastAPI, Depends
from typing import Annotated

from .routers import earthquakes
from .dependencies import get_earthquake_repository

app = FastAPI(
    title="Earthquake Monitor API",
    description="A simple earthquake monitoring system",
    version="0.1.0",
)

app.include_router(earthquakes.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}