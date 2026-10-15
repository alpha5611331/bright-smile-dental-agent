"""Top-level API router. Every route module is registered here under `/api`."""

from fastapi import APIRouter

from bright_smile.api.routes import auth, chat, health, leads, stats

API_PREFIX = "/api"

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(leads.router)
api_router.include_router(stats.router)
api_router.include_router(auth.router)
