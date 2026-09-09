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