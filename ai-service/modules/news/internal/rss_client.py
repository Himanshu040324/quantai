"""
Thin wrapper around Google News RSS. This is the ONLY file that should
fetch or parse RSS directly — router.py and service.py go through
fetch_headlines(), never httpx/feedparser directly. Same isolation
principle as yfinance_client.py in market_data, so swapping to NewsAPI
later (docx names it as the primary option) touches one file.
"""
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from modules.news.internal.constants import (
    GOOGLE_NEWS_RSS_TEMPLATE,
    MAX_ITEMS_PER_FETCH,
    TICKER_COMPANY_NAME,
)
from modules.news.internal.schemas import NewsItem

logger = logging.getLogger("quantai.news.rss")


class NewsFetchError(Exception):
    """Raised when the RSS feed can't be reached or parsed at all."""


def _build_query_url(ticker: str) -> str:
    company = TICKER_COMPANY_NAME.get(ticker, ticker)
    return GOOGLE_NEWS_RSS_TEMPLATE.format(query=httpx.QueryParams({"": company}).get(""))


def _parse_published(entry: dict) -> datetime:
    """
    feedparser gives both a struct_time (published_parsed) and a raw
    string (published). Prefer the struct_time; fall back to the raw
    string; fall back to "now" only if the feed genuinely omits both,
    rather than raising and losing an otherwise-valid headline.
    """
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, "published", None):
        try:
            return parsedate_to_datetime(entry.published).astimezone(timezone.utc)
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _fetch_raw_rss(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers={"User-Agent": "QuantAI/1.0"})
        response.raise_for_status()
        return response.content


async def fetch_headlines(ticker: str) -> list[NewsItem]:
    """
    Fetches and parses the Google News RSS feed for a ticker's mapped
    company name. Feed entries with unparseable required fields (no
    title/link) are skipped individually rather than failing the whole
    fetch — a handful of malformed entries shouldn't sink 29 good ones.
    """
    if ticker not in TICKER_COMPANY_NAME:
        raise NewsFetchError(f"No company-name mapping for ticker '{ticker}'")

    url = _build_query_url(ticker)

    try:
        raw = await _fetch_raw_rss(url)
    except httpx.HTTPError as exc:
        logger.warning("RSS fetch failed for %s: %s", ticker, exc)
        raise NewsFetchError(f"Failed to fetch RSS for '{ticker}': {exc}") from exc

    parsed = feedparser.parse(raw)
    if parsed.bozo and not parsed.entries:
        raise NewsFetchError(f"RSS feed for '{ticker}' could not be parsed")

    items: list[NewsItem] = []
    for entry in parsed.entries[:MAX_ITEMS_PER_FETCH]:
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)
        if not title or not link:
            continue
        items.append(
            NewsItem(
                title=title,
                link=link,
                published_at=_parse_published(entry),
                source=getattr(entry, "source", {}).get("title") if hasattr(entry, "source") else None,
            )
        )

    if not items:
        raise NewsFetchError(f"No usable headlines parsed for '{ticker}'")

    return items