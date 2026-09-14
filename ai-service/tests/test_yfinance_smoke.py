"""
Phase 0's original smoke test, formalized as a real pytest test rather
than a standalone script. Deliberately real network I/O against
yfinance — not mocked — which is why it's marked `network` and
excluded from the default run (see pytest.ini's `addopts`). Run it
explicitly with:

    pytest -m network tests/test_yfinance_smoke.py

Kept because it answers a genuinely different question than the
mocked endpoint tests below: "is yfinance itself still reachable and
returning sane data", not "does our caching/routing logic work".
"""
import pytest
import yfinance as yf

TICKER = "RELIANCE.NS"


@pytest.mark.network
def test_yfinance_pulls_five_years_of_data():
    data = yf.download(TICKER, period="5y", interval="1d", auto_adjust=False, progress=False)

    assert not data.empty, f"yfinance returned no data for {TICKER}"
    assert len(data) > 1000  # ~5 years of NSE trading days
    assert data.index.min() < data.index.max()