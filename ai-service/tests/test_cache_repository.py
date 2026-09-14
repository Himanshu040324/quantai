"""
Unit tests directly against cache_repository, bypassing HTTP entirely.
test_staleness_after_backdating_fetched_at below is deliberately the
exact scenario from the earlier staleness debugging session, turned
into a permanent regression test.
"""
from datetime import datetime, timedelta, timezone

from modules.market_data.internal import cache_repository
from modules.market_data.internal.schemas import OHLCVBar


def make_bar(date_str, close=100.0):
    return OHLCVBar(
        date=date_str, open=close, high=close, low=close,
        close=close, adj_close=close, volume=1000,
    )


async def test_is_stale_true_when_never_cached(db):
    assert await cache_repository.is_stale(db, "TEST.NOCACHE") is True


async def test_fresh_cache_is_not_stale(db):
    await cache_repository.upsert_bars(db, "TEST.FRESH", [make_bar("2026-01-01")])
    assert await cache_repository.is_stale(db, "TEST.FRESH") is False


async def test_upsert_is_idempotent_on_same_ticker_and_date(db):
    await cache_repository.upsert_bars(db, "TEST.DUP", [make_bar("2026-01-01", close=100.0)])
    await cache_repository.upsert_bars(db, "TEST.DUP", [make_bar("2026-01-01", close=105.0)])

    cached = await cache_repository.get_cached_bars(db, "TEST.DUP", years=1)
    assert len(cached) == 1  # (ticker, date) unique index -> updated, not duplicated
    assert cached[0].close == 105.0


async def test_staleness_after_backdating_fetched_at(db):
    """Regression test for the 25h-backdate scenario debugged manually earlier."""
    await cache_repository.upsert_bars(db, "TEST.STALE", [make_bar("2026-01-01")])
    assert await cache_repository.is_stale(db, "TEST.STALE") is False

    await db[cache_repository.COLLECTION_NAME].update_many(
        {"ticker": "TEST.STALE"},
        {"$set": {"fetched_at": datetime.now(timezone.utc) - timedelta(hours=25)}},
    )

    assert await cache_repository.is_stale(db, "TEST.STALE") is True