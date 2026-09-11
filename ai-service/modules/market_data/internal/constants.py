"""
Single source of truth for the candidate ticker universe.
Referenced by market_data (fetching) and, later, by optimization/
simulation modules — but only via market_data's public contract,
never by importing this file directly from outside the module.
"""

TICKER_UNIVERSE: list[str] = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "NIFTYBEES.NS",
    "AAPL",
    "MSFT",
    "NVDA",
]

# OHLCV: daily prices move constantly -> short freshness window.
OHLCV_STALENESS_HOURS = 24

# Fundamentals: P/E, earnings growth update quarterly/slowly ->
# no point re-hitting yfinance every day for these.
FUNDAMENTALS_STALENESS_HOURS = 24 * 7  # 7 days