from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app import models
from app.database import engine
from app.routers import complaints


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Create database tables when the application starts.
    """

    models.Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="Fraud Intelligence API",
    description="Banking complaint and fraud intelligence management system.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
)
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "fraud-intelligence-api",
    }


app.include_router(complaints.router)