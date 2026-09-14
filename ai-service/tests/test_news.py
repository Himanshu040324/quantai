from datetime import datetime, timezone

from modules.news.internal.rss_client import NewsFetchError
from modules.news.internal.schemas import NewsItem


def make_item(link="https://example.com/1"):
    return NewsItem(
        title="Test Headline", link=link, published_at=datetime.now(timezone.utc), source="Test Wire"
    )


async def test_first_fetch_is_live(client, db, monkeypatch):
    async def fake_fetch_headlines(ticker):
        return [make_item()]

    monkeypatch.setattr("modules.news.internal.service.fetch_headlines", fake_fetch_headlines)

    res = await client.get("/news/AAPL")
    assert res.status_code == 200
    assert res.json()["source"] == "live"


async def test_second_fetch_is_cached(client, db, monkeypatch):
    calls = {"n": 0}

    async def fake_fetch_headlines(ticker):
        calls["n"] += 1
        return [make_item(link=f"https://example.com/{calls['n']}")]

    monkeypatch.setattr("modules.news.internal.service.fetch_headlines", fake_fetch_headlines)

    await client.get("/news/AAPL")
    res = await client.get("/news/AAPL")

    assert res.json()["source"] == "cache"
    assert calls["n"] == 1


async def test_unsupported_ticker_returns_400(client, db):
    res = await client.get("/news/NOTINUNIVERSE")
    assert res.status_code == 400


async def test_rss_fetch_error_returns_502(client, db, monkeypatch):
    async def failing(ticker):
        raise NewsFetchError("feed unreachable")

    monkeypatch.setattr("modules.news.internal.service.fetch_headlines", failing)

    res = await client.get("/news/AAPL")
    assert res.status_code == 502