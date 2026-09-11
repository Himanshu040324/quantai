"""
News module constants. Google News RSS is used per the docx's
"NewsAPI or RSS" option — no API key needed, and its query search
works for both US tickers and .NS-suffixed Indian tickers once mapped
to a plain company name (RSS search on "RELIANCE.NS" as a literal
string returns poor results; "Reliance Industries" does not).
"""

# Static, deterministic mapping — not invented data, just the plain-
# English company name Google News search actually needs per ticker.
TICKER_COMPANY_NAME: dict[str, str] = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "NIFTYBEES.NS": "Nippon India ETF Nifty BeES",
    "AAPL": "Apple Inc",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
}

GOOGLE_NEWS_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

RETENTION_DAYS = 30          # docx: "last 30 days of headlines per ticker"
NEWS_STALENESS_HOURS = 24    # re-check the feed once a day per ticker
MAX_ITEMS_PER_FETCH = 30     # cap how many entries we persist per fetch, avoid unbounded growth