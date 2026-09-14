"""
Shared fixtures for the ai-service pytest suite.

Hard safety rule: tests run ONLY against MONGODB_DB_NAME=quantai_test,
never the dev 'quantai' database. The env var is force-set before any
of ai-service's modules are imported (Settings is @lru_cache'd, so
this has to happen first), and _db_connection asserts the connected
database name as a second line of defense.

Event loop note: AsyncIOMotorClient binds its background tasks to the
event loop active at creation time. Session-wide loop consistency is
handled by pytest.ini's asyncio_default_fixture_loop_scope/
asyncio_default_test_loop_scope = session settings — NOT by an
event_loop fixture override here. That override pattern is deprecated
in modern pytest-asyncio (and outright breaks against newer pytest
versions, which access fixture internals pytest-asyncio 0.21.x
depended on differently). Keep requirements.txt's pytest-asyncio>=0.24
pin in place; older versions don't support the ini-based loop scope
config used here.
"""
import os
import sys
from pathlib import Path

# Force the test database BEFORE importing anything that calls
# get_settings() — must happen before `from main import app` below.
os.environ["MONGODB_DB_NAME"] = "quantai_test"

# Allow `pytest` to be run from ai-service/ and still resolve
# top-level packages (shared, modules).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from modules.market_data.internal.cache_repository import (
    ensure_indexes as ensure_ohlcv_indexes,
)
from modules.market_data.internal.fundamentals_repository import (
    ensure_indexes as ensure_fundamentals_indexes,
)
from modules.news.internal.cache_repository import ensure_indexes as ensure_news_indexes
from shared.db.connection import close_mongo_connection, connect_to_mongo, get_database


@pytest_asyncio.fixture(scope="session")
async def _db_connection():
    """
    One real Motor connection for the whole test session, against
    quantai_test only. Indexes are created once here (mirrors what
    main.py's lifespan does), and the entire test database is dropped
    at the end of the session so no test data survives between runs.
    """
    await connect_to_mongo()
    db = get_database()

    assert db.name == "quantai_test", (
        f"Refusing to run tests against database '{db.name}' — "
        "tests must run against 'quantai_test' only."
    )

    await ensure_ohlcv_indexes(db)
    await ensure_fundamentals_indexes(db)
    await ensure_news_indexes(db)

    yield db

    await db.client.drop_database(db.name)
    await close_mongo_connection()


@pytest_asyncio.fixture
async def db(_db_connection):
    """
    Per-test handle to quantai_test. Clears all collections' documents
    after each test (not the whole DB — indexes stay put) so
    cache-hit/miss assertions never depend on leftover data from a
    previous test.
    """
    yield _db_connection
    for name in await _db_connection.list_collection_names():
        await _db_connection[name].delete_many({})


@pytest_asyncio.fixture
async def client(_db_connection):
    """
    Async HTTP client bound directly to the FastAPI app via
    ASGITransport — no real socket/port needed. Lifespan is not
    triggered through this transport, which is fine: _db_connection
    already did the equivalent setup (connect + ensure_indexes).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac