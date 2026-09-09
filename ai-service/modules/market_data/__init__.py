"""
Public contract for the market_data module.

Other modules and main.py should import ONLY from here — never reach
into modules.market_data.internal.* directly. This mirrors the
backend/src/modules/*/index.js boundary rule from the Master Prompt.

Currently exposes only `router`. Step 2 will add the real OHLCV
endpoints to internal/router.py; Step 4 adds fundamentals the same way.
"""
from modules.market_data.internal.router import router

__all__ = ["router"]