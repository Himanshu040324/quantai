"""
Public contract for the optimization module.

Other modules and main.py should import ONLY from here — never reach
into modules.optimization.internal.* directly.

Step 1 exposes only `router`, with a single diagnostic endpoint to
verify the covariance pipeline independently before CVXPY (Step 2)
consumes it.
"""
from modules.optimization.internal.router import router

__all__ = ["router"]