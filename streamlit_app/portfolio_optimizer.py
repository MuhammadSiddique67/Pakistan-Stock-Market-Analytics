"""
portfolio_optimizer.py

Portfolio optimization using scipy.optimize.minimize (SLSQP).

Constraints used throughout:
- Weights sum to 1.0 (fully invested)
- Long-only (no short selling)
- Each weight in [0, 1]

Includes Maximum Sharpe Ratio optimization, Minimum Volatility optimization,
an exact constrained Efficient Frontier curve, and a random-portfolio
Monte Carlo simulation for visualization purposes.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple

TRADING_DAYS_PER_YEAR = 252


# ------------------------------------------------------------------
# Core portfolio math
# ------------------------------------------------------------------

def portfolio_return(weights: np.ndarray, expected_returns: pd.Series) -> float:
    return float(np.dot(weights, expected_returns))


def portfolio_volatility(weights: np.ndarray, cov_matrix: pd.DataFrame) -> float:
    variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    return float(np.sqrt(max(variance, 0)))


def portfolio_sharpe(weights: np.ndarray, expected_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float) -> float:
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, cov_matrix)
    if vol == 0:
        return 0.0
    return (ret - risk_free_rate) / vol


def _bounds(n_assets: int) -> Tuple:
    return tuple((0.0, 1.0) for _ in range(n_assets))


def _weight_sum_constraint() -> Dict:
    return {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}


def _initial_guess(n_assets: int) -> np.ndarray:
    return np.repeat(1.0 / n_assets, n_assets)


# ------------------------------------------------------------------
# Maximum Sharpe Ratio
# ------------------------------------------------------------------

def optimize_max_sharpe(
    expected_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float
) -> Dict:
    n_assets = len(expected_returns)

    def negative_sharpe(weights):
        return -portfolio_sharpe(weights, expected_returns, cov_matrix, risk_free_rate)

    result = minimize(
        negative_sharpe,
        _initial_guess(n_assets),
        method="SLSQP",
        bounds=_bounds(n_assets),
        constraints=[_weight_sum_constraint()],
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not result.success:
        raise ValueError(f"Maximum Sharpe optimization failed to converge: {result.message}")

    weights = result.x
    weights = np.clip(weights, 0, 1)
    weights = weights / weights.sum()

    return {
        "weights": pd.Series(weights, index=expected_returns.index),
        "expected_return": portfolio_return(weights, expected_returns),
        "volatility": portfolio_volatility(weights, cov_matrix),
        "sharpe_ratio": portfolio_sharpe(weights, expected_returns, cov_matrix, risk_free_rate),
    }


# ------------------------------------------------------------------
# Minimum Volatility
# ------------------------------------------------------------------

def optimize_min_volatility(expected_returns: pd.Series, cov_matrix: pd.DataFrame) -> Dict:
    n_assets = len(expected_returns)

    def variance(weights):
        return portfolio_volatility(weights, cov_matrix) ** 2

    result = minimize(
        variance,
        _initial_guess(n_assets),
        method="SLSQP",
        bounds=_bounds(n_assets),
        constraints=[_weight_sum_constraint()],
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not result.success:
        raise ValueError(f"Minimum Volatility optimization failed to converge: {result.message}")

    weights = result.x
    weights = np.clip(weights, 0, 1)
    weights = weights / weights.sum()

    return {
        "weights": pd.Series(weights, index=expected_returns.index),
        "expected_return": portfolio_return(weights, expected_returns),
        "volatility": portfolio_volatility(weights, cov_matrix),
    }


# ------------------------------------------------------------------
# Exact constrained Efficient Frontier
# ------------------------------------------------------------------

def optimize_for_target_return(
    expected_returns: pd.Series, cov_matrix: pd.DataFrame, target_return: float
) -> Dict:
    """Find the minimum-volatility portfolio that achieves a specific
    target expected return. Used to trace the exact efficient frontier."""
    n_assets = len(expected_returns)

    def variance(weights):
        return portfolio_volatility(weights, cov_matrix) ** 2

    constraints = [
        _weight_sum_constraint(),
        {"type": "eq", "fun": lambda w: portfolio_return(w, expected_returns) - target_return},
    ]

    result = minimize(
        variance,
        _initial_guess(n_assets),
        method="SLSQP",
        bounds=_bounds(n_assets),
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not result.success:
        return None

    weights = np.clip(result.x, 0, 1)
    if weights.sum() == 0:
        return None
    weights = weights / weights.sum()

    return {
        "weights": pd.Series(weights, index=expected_returns.index),
        "expected_return": portfolio_return(weights, expected_returns),
        "volatility": portfolio_volatility(weights, cov_matrix),
    }


def calculate_efficient_frontier(
    expected_returns: pd.Series, cov_matrix: pd.DataFrame, n_points: int = 50
) -> pd.DataFrame:
    """
    Trace the exact efficient frontier by minimizing volatility across a
    range of target returns spanning the min-to-max achievable individual
    asset returns.
    """
    min_ret = float(expected_returns.min())
    max_ret = float(expected_returns.max())
    target_returns = np.linspace(min_ret, max_ret, n_points)

    frontier_points = []
    for target in target_returns:
        result = optimize_for_target_return(expected_returns, cov_matrix, target)
        if result is not None:
            frontier_points.append({
                "target_return": result["expected_return"],
                "volatility": result["volatility"],
            })

    frontier_df = pd.DataFrame(frontier_points)
    if not frontier_df.empty:
        frontier_df = frontier_df.sort_values("volatility").reset_index(drop=True)
    return frontier_df


# ------------------------------------------------------------------
# Monte Carlo random-portfolio simulation
# ------------------------------------------------------------------

def monte_carlo_simulation(
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
    n_portfolios: int = 8000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate random long-only portfolios (weights summing to 1) and compute
    their expected return, volatility, and Sharpe Ratio. Used to visualize
    the feasible-portfolio cloud behind the efficient frontier curve.
    """
    rng = np.random.default_rng(seed)
    n_assets = len(expected_returns)

    results = np.zeros((n_portfolios, 3))
    weight_records = np.zeros((n_portfolios, n_assets))

    ret_arr = expected_returns.values
    cov_arr = cov_matrix.values

    for i in range(n_portfolios):
        weights = rng.random(n_assets)
        weights /= weights.sum()

        port_ret = np.dot(weights, ret_arr)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_arr, weights)))
        sharpe = (port_ret - risk_free_rate) / port_vol if port_vol > 0 else 0.0

        results[i] = [port_ret, port_vol, sharpe]
        weight_records[i] = weights

    sim_df = pd.DataFrame(results, columns=["expected_return", "volatility", "sharpe_ratio"])
    weights_df = pd.DataFrame(weight_records, columns=expected_returns.index)
    return pd.concat([sim_df, weights_df], axis=1)
