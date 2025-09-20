from fastapi import FastAPI

from .routers import earthquakes

app = FastAPI(
    title="Earthquake Monitor API",
    description="A simple earthquake monitoring system",
    version="0.1.0",
)

app.include_router(earthquakes.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
