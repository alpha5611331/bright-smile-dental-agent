"""MongoDB connection lifecycle (PyMongo async client + Beanie)."""

from typing import Any

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from bright_smile.core.config import Settings
from bright_smile.db.documents.conversation import Conversation

# PyMongo types documents as dict[str, Any]; Beanie models provide the typed layer on top.
type MongoClient = AsyncMongoClient[dict[str, Any]]

# Beanie document models are registered here as they are introduced (SPEC section 6).
DOCUMENT_MODELS: list[type[Document]] = [Conversation]


def create_client(settings: Settings) -> MongoClient:
    return AsyncMongoClient(
        settings.mongodb_uri.get_secret_value(),
        tz_aware=True,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        appname="bright-smile-backend",
    )


async def init_db(client: MongoClient, settings: Settings) -> None:
    await init_beanie(database=client[settings.mongodb_db], document_models=DOCUMENT_MODELS)


async def ping(client: MongoClient) -> bool:
    """Return True when the server answers a ping within the server selection timeout."""
    try:
        await client.admin.command("ping")
    except PyMongoError:
        return False
    return True
