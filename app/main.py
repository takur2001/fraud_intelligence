from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models
from app.database import engine
from app.routers import auth, complaints


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Create database tables when the application starts.
    """

    models.Base.metadata.create_all(
        bind=engine
    )

    yield


app = FastAPI(
    title="Fraud Intelligence API",
    description=(
        "Banking complaint and fraud intelligence "
        "management system."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/",
    tags=["System"],
    summary="API welcome",
)
def root() -> dict[str, str]:
    """
    Return basic information about the deployed API.
    """

    return {
        "message": "Fraud Intelligence API is running.",
        "health": "/health",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
)
def health_check() -> dict[str, str]:
    """
    Check whether the API is running.
    """

    return {
        "status": "healthy",
        "service": "fraud-intelligence-api",
    }


app.include_router(
    complaints.router
)

app.include_router(
    auth.router
)
