"""
Public contract for the market_data module.

Other modules and main.py should import ONLY from here — never reach
into modules.market_data.internal.* directly. This mirrors the
backend/src/modules/*/index.js boundary rule from the Master Prompt.

Exposes:
- `router`: FastAPI router with OHLCV/fundamentals endpoints.
- `TICKER_UNIVERSE`: the candidate ticker list, re-exported so other
  modules (optimization, simulation, ...) don't hardcode their own
  copy or reach into internal/constants.py directly.
- `get_ohlcv_cached`: cache-first OHLCV accessor, re-exported so other
  modules can pull price history without importing internal/service.py
  directly.
"""
from modules.market_data.internal.constants import TICKER_UNIVERSE
from modules.market_data.internal.router import router
from modules.market_data.internal.service import get_ohlcv_cached

__all__ = ["router", "TICKER_UNIVERSE", "get_ohlcv_cached"]