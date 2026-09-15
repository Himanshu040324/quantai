"""
Pure CVXPY optimization logic: mean_returns + covariance in, portfolio
weights out. No I/O, no Mongo, no FastAPI — testable in isolation with
known inputs/outputs.

Three solve modes, all sharing the same constraint set (sum(w)=1, w>=0,
w<=MAX_SINGLE_ASSET_WEIGHT):
- solve_markowitz: utility-form (Step 2) — maximize return - lambda*variance
- solve_min_variance: minimize variance, no return target — frontier's left edge
- solve_max_return: maximize return — frontier's right edge
- solve_target_return: minimize variance subject to a fixed target return —
  used to sweep the frontier between the two edges (Step 3)
"""
import logging

import cvxpy as cp
import numpy as np

from modules.optimization.internal.constants import MAX_SINGLE_ASSET_WEIGHT

logger = logging.getLogger("quantai.optimization.solver")


class OptimizationError(Exception):
    """Raised when the QP is infeasible or the solver fails to converge."""


class SolverResult:
    def __init__(self, weights: np.ndarray, expected_return: float, expected_variance: float):
        self.weights = weights
        self.expected_return = expected_return
        self.expected_variance = expected_variance


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


def _solve_and_extract(
    problem: cp.Problem, w: cp.Variable, mean_returns: np.ndarray, covariance: np.ndarray
) -> SolverResult:
    try:
        problem.solve()
    except cp.error.SolverError as exc:
        logger.error("CVXPY solver raised: %s", exc)
        raise OptimizationError(f"Solver failed: {exc}") from exc

    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        logger.error("Solver returned non-optimal status: %s", problem.status)
        raise OptimizationError(f"Optimization did not converge: status={problem.status}")

    if problem.status == cp.OPTIMAL_INACCURATE:
        logger.warning("Solver converged with OPTIMAL_INACCURATE status — result may be imprecise")

    weights = np.asarray(w.value).flatten()
    # Numerical solvers can leave tiny negative residuals or sums slightly
    # off 1.0 — clip and renormalize rather than exposing solver noise as
    # a fabricated negative weight in the response.
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum()

    expected_return = float(mean_returns @ weights)
    expected_variance = float(weights @ covariance @ weights)

    return SolverResult(weights=weights, expected_return=expected_return, expected_variance=expected_variance)


def solve_markowitz(
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    risk_lambda: float,
) -> SolverResult:
    """
    Solves: maximize (mean_returns @ w - risk_lambda * w @ covariance @ w)
    subject to the base constraints.
    """
    n = len(mean_returns)
    if covariance.shape != (n, n):
        raise OptimizationError(
            f"Shape mismatch: mean_returns has {n} assets, covariance is {covariance.shape}"
        )
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    portfolio_return = mean_returns @ w
    portfolio_variance = cp.quad_form(w, covariance)
    objective = cp.Maximize(portfolio_return - risk_lambda * portfolio_variance)
    problem = cp.Problem(objective, _base_constraints(w))

    return _solve_and_extract(problem, w, mean_returns, covariance)


def solve_min_variance(mean_returns: np.ndarray, covariance: np.ndarray) -> SolverResult:
    """Minimizes variance with no return target — the frontier's left edge."""
    n = len(mean_returns)
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    objective = cp.Minimize(cp.quad_form(w, covariance))
    problem = cp.Problem(objective, _base_constraints(w))

    return _solve_and_extract(problem, w, mean_returns, covariance)


def solve_max_return(mean_returns: np.ndarray, covariance: np.ndarray) -> SolverResult:
    """Maximizes expected return subject to the same constraints — the frontier's right edge."""
    n = len(mean_returns)
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    objective = cp.Maximize(mean_returns @ w)
    problem = cp.Problem(objective, _base_constraints(w))

    return _solve_and_extract(problem, w, mean_returns, covariance)


def solve_target_return(
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    target_return: float,
) -> SolverResult:
    """
    Minimizes variance subject to achieving at least `target_return`.
    Used to sweep intermediate points on the frontier between the
    min-variance and max-return edges.
    """
    n = len(mean_returns)
    _check_feasible_by_construction(n)

    w = cp.Variable(n)
    objective = cp.Minimize(cp.quad_form(w, covariance))
    constraints = _base_constraints(w) + [mean_returns @ w >= target_return]
    problem = cp.Problem(objective, constraints)

    return _solve_and_extract(problem, w, mean_returns, covariance)