from modules.market_data.internal.schemas import FundamentalsData
from modules.market_data.internal.yfinance_client import TickerFetchError


async def test_first_fetch_is_live(client, db, monkeypatch):
    async def fake_fetch_fundamentals(ticker):
        return FundamentalsData(pe_ratio=28.5, forward_pe=25.1, sector="Technology")

    monkeypatch.setattr(
        "modules.market_data.internal.service.fetch_fundamentals", fake_fetch_fundamentals
    )

    res = await client.get("/market-data/fundamentals/TESTX")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "live"
    assert body["data"]["pe_ratio"] == 28.5


async def test_second_fetch_is_cached(client, db, monkeypatch):
    calls = {"n": 0}

    async def fake_fetch_fundamentals(ticker):
        calls["n"] += 1
        return FundamentalsData(pe_ratio=28.5)

    monkeypatch.setattr(
        "modules.market_data.internal.service.fetch_fundamentals", fake_fetch_fundamentals
    )

    await client.get("/market-data/fundamentals/TESTX")
    res = await client.get("/market-data/fundamentals/TESTX")

    assert res.json()["source"] == "cache"
    assert calls["n"] == 1


async def test_missing_fields_stay_null_not_fabricated(client, db, monkeypatch):
    """ETF-like ticker (e.g. NIFTYBEES.NS) — missing fields must be null, never defaulted to 0."""
    async def fake_fetch_fundamentals(ticker):
        return FundamentalsData()  # everything None, as a real ETF response would be

    monkeypatch.setattr(
        "modules.market_data.internal.service.fetch_fundamentals", fake_fetch_fundamentals
    )

    res = await client.get("/market-data/fundamentals/ETFTEST")
    data = res.json()["data"]
    assert data["pe_ratio"] is None
    assert data["market_cap"] is None


async def test_fetch_error_returns_502(client, db, monkeypatch):
    async def failing(ticker):
        raise TickerFetchError("no info")

    monkeypatch.setattr("modules.market_data.internal.service.fetch_fundamentals", failing)

    res = await client.get("/market-data/fundamentals/BADTICKER")
    assert res.status_code == 502