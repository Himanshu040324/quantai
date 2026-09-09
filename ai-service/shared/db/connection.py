"""
Async MongoDB connection for ai-service, via Motor.

Deliberately separate from backend/'s Mongoose connection — same Atlas
cluster and database, two different drivers/languages talking to it.
Modules must import get_database() from here rather than instantiating
their own client, so there is exactly one connection pool per process.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from shared.config import get_settings

logger = logging.getLogger("quantai.db")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Call once on FastAPI startup."""
    global _client, _db
    settings = get_settings()

    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]

    # Fail fast on startup if Atlas isn't reachable, rather than on first request.
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    """Call once on FastAPI shutdown."""
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency-injectable accessor. Raises clearly if called before
    connect_to_mongo() has run, instead of failing with a confusing
    'NoneType has no attribute' error deep in a module.
    """
    if _db is None:
        raise RuntimeError(
            "MongoDB connection not initialized. "
            "connect_to_mongo() must run during FastAPI startup."
        )
    return _db