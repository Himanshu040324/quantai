"""
CVaR (Conditional Value at Risk) optimization via the Rockafellar-Uryasev
formulation — a linear program over historical return scenarios, distinct
from solver.py's mean-variance QPs.

CVaR at confidence level beta (e.g. 95%) is the expected loss in the
worst (1 - beta) fraction of scenarios. Unlike variance, it specifically
targets tail risk rather than penalizing upside and downside symmetrically
— this is the "more tail-risk-aware" option called for in the plan.

Kept as a separate module from solver.py (mean/covariance QPs) since the
formulation is structurally different: it operates on raw scenario
returns, not summary statistics, and introduces auxiliary variables
(VaR threshold + per-scenario shortfall) that mean-variance doesn't need.
"""
import logging

import cvxpy as cp
import numpy as np

from modules.optimization.internal.constants import CVAR_CONFIDENCE_LEVEL, MAX_SINGLE_ASSET_WEIGHT
from modules.optimization.internal.solver import OptimizationError, SolverResult

logger = logging.getLogger("quantai.optimization.cvar_solver")


def _base_constraints(w: cp.Variable) -> list:
    return [
        cp.sum(w) == 1,
        w >= 0,
        w <= MAX_SINGLE_ASSET_WEIGHT,
    ]


def _check_feasible_by_construction(n: int) -> None:
    if n * MAX_SINGLE_ASSET_WEIGHT < 1.0:
        raise OptimizationError(
            f"Infeasible constraints: {n} assets with {MAX_SINGLE_ASSET_WEIGHT:.0%} cap each "
            f"can sum to at most {n * MAX_SINGLE_ASSET_WEIGHT:.0%}, need 100%"
        )


def _extract_result(
    problem: cp.Problem,
    w: cp.Variable,
    scenario_returns: np.ndarray,
    mean_returns: np.ndarray,
    covariance: np.ndarray,
) -> tuple[SolverResult, float]:
    """
    Returns (SolverResult, cvar_value). SolverResult.expected_variance is
    populated from the covariance matrix for comparability with Markowitz
    results, even though CVaR's own objective doesn't use variance directly.
    """
    try:
        problem.solve()
    except cp.error.SolverError as exc:
        logger.error("CVXPY CVaR solver raised: %s", exc)
        raise OptimizationError(f"Solver failed: {exc}") from exc

    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        logger.error("CVaR solver returned non-optimal status: %s", problem.status)
        raise OptimizationError(f"CVaR optimization did not converge: status={problem.status}")

    if problem.status == cp.OPTIMAL_INACCURATE:
        logger.warning("CVaR solver converged with OPTIMAL_INACCURATE status — result may be imprecise")

    weights = np.asarray(w.value).flatten()
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum()

    expected_return = float(mean_returns @ weights)
    expected_variance = float(weights @ covariance @ weights)
    portfolio_scenarios = scenario_returns @ weights
    cvar_value = _historical_cvar(portfolio_scenarios, CVAR_CONFIDENCE_LEVEL)

    return SolverResult(weights=weights, expected_return=expected_return, expected_variance=expected_variance), cvar_value


def _historical_cvar(portfolio_scenario_returns: np.ndarray, beta: float) -> float:
    """
    Realized CVaR from the achieved weights, computed directly from the
    historical scenario returns (not the LP's internal VaR variable) —
    used for reporting the actual result, independent of solver internals.
    """
    losses = -portfolio_scenario_returns
    var_threshold = np.percentile(losses, beta * 100)
    tail_losses = losses[losses >= var_threshold]
    if len(tail_losses) == 0:
        return float(var_threshold)
    return float(tail_losses.mean())


def solve_min_cvar(
    scenario_returns: np.ndarray,
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    beta: float = CVAR_CONFIDENCE_LEVEL,
) -> tuple[SolverResult, float]:
    """
    Minimizes CVaR at confidence level beta, no return target — the
    CVaR-frontier's low-risk edge. scenario_returns is T x N (T scenarios,
    N assets), typically the aligned historical daily log returns.

    Rockafellar-Uryasev LP formulation:
      minimize  zeta + (1 / (T * (1-beta))) * sum(u_t)
      subject to  u_t >= -scenario_returns[t] @ w - zeta,  u_t >= 0
                  (plus the base weight constraints)
    where zeta is the VaR threshold (auxiliary variable) and u_t is the
    per-scenario shortfall beyond it.
    """
    t, n = scenario_returns.shape
    if mean_returns.shape != (n,) or covariance.shape != (n, n):
        raise OptimizationError(
            f"Shape mismatch: scenario_returns has {n} assets, "
            f"mean_returns={mean_returns.shape}, covariance={covariance.shape}"
        )
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    zeta = cp.Variable()
    u = cp.Variable(t)

    portfolio_losses = -scenario_returns @ w
    cvar_expr = zeta + (1.0 / (t * (1 - beta))) * cp.sum(u)

    constraints = _base_constraints(w) + [
        u >= portfolio_losses - zeta,
        u >= 0,
    ]

    problem = cp.Problem(cp.Minimize(cvar_expr), constraints)

    return _extract_result(problem, w, scenario_returns, mean_returns, covariance)


def solve_cvar_target_return(
    scenario_returns: np.ndarray,
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    target_return: float,
    beta: float = CVAR_CONFIDENCE_LEVEL,
) -> tuple[SolverResult, float]:
    """
    Minimizes CVaR subject to achieving at least `target_return` (annualized,
    same units as mean_returns). Mirrors solve_target_return's role in the
    mean-variance frontier, but for CVaR — used to pick a point on the
    CVaR strategy comparable to the risk_lambda-driven Markowitz recommendation.
    """
    t, n = scenario_returns.shape
    if mean_returns.shape != (n,) or covariance.shape != (n, n):
        raise OptimizationError(
            f"Shape mismatch: scenario_returns has {n} assets, "
            f"mean_returns={mean_returns.shape}, covariance={covariance.shape}"
        )
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    zeta = cp.Variable()
    u = cp.Variable(t)

    portfolio_losses = -scenario_returns @ w
    cvar_expr = zeta + (1.0 / (t * (1 - beta))) * cp.sum(u)

    constraints = _base_constraints(w) + [
        u >= portfolio_losses - zeta,
        u >= 0,
        mean_returns @ w >= target_return,
    ]

    problem = cp.Problem(cp.Minimize(cvar_expr), constraints)

    return _extract_result(problem, w, scenario_returns, mean_returns, covariance)