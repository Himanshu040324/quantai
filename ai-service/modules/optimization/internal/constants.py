"""
Fixed optimizer constraints, per the Phase 3 plan: budget = 100%,
no short-selling, max 25% single-asset cap. Kept as constants (not
request parameters) to keep OptimizeRequest minimal — revisit if a
later phase needs per-request overrides.
"""

MAX_SINGLE_ASSET_WEIGHT = 0.25