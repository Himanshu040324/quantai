"""
Fixed optimizer constraints, per the Phase 3 plan: budget = 100%,
no short-selling, max 25% single-asset cap. Kept as constants (not
request parameters) to keep request schemas minimal — revisit if a
later phase needs per-request overrides.
"""

MAX_SINGLE_ASSET_WEIGHT = 0.25

# CVaR confidence level — industry-standard 95%. Same rationale as the
# 25% cap: fixed for now, not exposed as a request parameter.
CVAR_CONFIDENCE_LEVEL = 0.95