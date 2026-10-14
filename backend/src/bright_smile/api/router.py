"""Top-level API router. Every route module is registered here under `/api`."""

from fastapi import APIRouter

from bright_smile.api.routes import health

API_PREFIX = "/api"

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(health.router)
