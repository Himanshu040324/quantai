"""
Endpoint tests for OHLCV routes, via the real FastAPI app + real
quantai_test Mongo, with yfinance itself mocked at the one file
(yfinance_client.py) that's allowed to import it — so these tests are
fast and never flaky due to network/Yahoo throttling.
"""
from modules.market_data.internal.schemas import OHLCVBar
from modules.market_data.internal.yfinance_client import TickerFetchError


def make_bar(date_str, close=100.0):
    return OHLCVBar(
        date=date_str, open=close, high=close, low=close,
        close=close, adj_close=close, volume=1000,
    )


async def test_first_fetch_is_live(client, db, monkeypatch):
    async def fake_fetch_ohlcv(ticker, years=5):
        return [make_bar("2026-01-01")]

    monkeypatch.setattr("modules.market_data.internal.service.fetch_ohlcv", fake_fetch_ohlcv)

    res = await client.get("/market-data/ohlcv/TESTX", params={"years": 1})
    assert res.status_code == 200
    assert res.json()["source"] == "live"
    assert res.json()["bar_count"] == 1


async def test_second_fetch_is_cache_hit_and_skips_yfinance(client, db, monkeypatch):
    calls = {"n": 0}

    async def fake_fetch_ohlcv(ticker, years=5):
        calls["n"] += 1
        return [make_bar("2026-01-01")]

    monkeypatch.setattr("modules.market_data.internal.service.fetch_ohlcv", fake_fetch_ohlcv)

    await client.get("/market-data/ohlcv/TESTX", params={"years": 1})
    res = await client.get("/market-data/ohlcv/TESTX", params={"years": 1})

    assert res.json()["source"] == "cache"
    assert calls["n"] == 1  # yfinance mock only ever called once


async def test_ticker_fetch_error_returns_502(client, db, monkeypatch):
    async def failing(ticker, years=5):
        raise TickerFetchError("no data")

    monkeypatch.setattr("modules.market_data.internal.service.fetch_ohlcv", failing)

    res = await client.get("/market-data/ohlcv/BADTICKER", params={"years": 1})
    assert res.status_code == 502


async def test_years_out_of_range_returns_400(client, db):
    res = await client.get("/market-data/ohlcv/AAPL", params={"years": 99})
    assert res.status_code == 400


async def test_universe_fetch_reports_per_ticker_success_and_failure(client, db, monkeypatch):
    async def fake_fetch_ohlcv(ticker, years=5):
        if ticker == "NVDA":
            raise TickerFetchError("simulated failure")
        return [make_bar("2026-01-01")]

    monkeypatch.setattr("modules.market_data.internal.service.fetch_ohlcv", fake_fetch_ohlcv)

    res = await client.post("/market-data/ohlcv/universe/fetch", params={"years": 1})
    body = res.json()
    assert body["succeeded"] == 7
    assert body["failed"] == 1
    assert any(r["ticker"] == "NVDA" and r["status"] == "failed" for r in body["results"])