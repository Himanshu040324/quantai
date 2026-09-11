"""
FastAPI entrypoint for ai-service.
Owns app lifecycle (Mongo connect/disconnect, index creation) and module mounting.
Route logic itself always lives inside modules/, never here.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from modules.market_data import router as market_data_router
from modules.market_data.internal.cache_repository import ensure_indexes as ensure_ohlcv_indexes
from modules.market_data.internal.fundamentals_repository import (
    ensure_indexes as ensure_fundamentals_indexes,
)
from shared.db.connection import close_mongo_connection, connect_to_mongo, get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    db = get_database()
    await ensure_ohlcv_indexes(db)
    await ensure_fundamentals_indexes(db)
    yield
    await close_mongo_connection()


app = FastAPI(title="QuantAI AI Service", lifespan=lifespan)

app.include_router(market_data_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db():
    db = get_database()
    await db.command("ping")
    return {"status": "ok", "database": db.name}