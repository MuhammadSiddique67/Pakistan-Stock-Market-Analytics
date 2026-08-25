"""
analytics.py

Core financial analytics calculations: returns, volatility, Sharpe ratio,
covariance/correlation, Beta, Maximum Drawdown, hypothetical future values,
and historical backtesting metrics.

All calculations operate on real historical price data supplied by
data_fetcher.py. No values in this module are hard-coded.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple

TRADING_DAYS_PER_YEAR = 252


# ------------------------------------------------------------------
# Returns
# ------------------------------------------------------------------

def calculate_daily_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    # Calculate daily percentage returns from stock prices
    returns = price_df.pct_change(fill_method=None)

    # Replace extreme daily returns above +50% or below -50% with NaN
    returns = returns.mask(returns.abs() > 0.5)

    # Return the cleaned daily returns
    return returns


def average_daily_return(returns_df: pd.DataFrame) -> pd.Series:
    return returns_df.mean()


def daily_volatility(returns_df: pd.DataFrame) -> pd.Series:
    return returns_df.std()


def expected_annual_return(returns_df: pd.DataFrame) -> pd.Series:
    """Mean daily return x 252."""
    return returns_df.mean() * TRADING_DAYS_PER_YEAR


def annual_volatility(returns_df: pd.DataFrame) -> pd.Series:
    """Std of daily returns x sqrt(252)."""
    return returns_df.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def annualized_covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.cov() * TRADING_DAYS_PER_YEAR


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.corr()


# ------------------------------------------------------------------
# Risk-adjusted performance
# ------------------------------------------------------------------

def sharpe_ratios(returns_df: pd.DataFrame, risk_free_rate: float) -> pd.Series:
    """Per-asset Sharpe Ratio using annualized return and volatility."""
    ann_return = expected_annual_return(returns_df)
    ann_vol = annual_volatility(returns_df)
    ann_vol_safe = ann_vol.replace(0, np.nan)
    sharpe = (ann_return - risk_free_rate) / ann_vol_safe
    return sharpe.fillna(0.0)


def portfolio_sharpe_ratio(port_return: float, port_vol: float, risk_free_rate: float) -> float:
    if port_vol == 0 or np.isnan(port_vol):
        return 0.0
    return (port_return - risk_free_rate) / port_vol


# ------------------------------------------------------------------
# Maximum Drawdown
# ------------------------------------------------------------------

def calculate_max_drawdown(cumulative_values: pd.Series) -> Tuple[float, pd.Series]:
    """
    Maximum Drawdown = min( CumValue / RunningPeak - 1 ).

    Returns (max_drawdown, drawdown_series) so callers can chart the
    drawdown-over-time curve as well as report the single worst value.
    """
    running_peak = cumulative_values.cummax()
    drawdown_series = cumulative_values / running_peak - 1
    max_dd = drawdown_series.min()
    return float(max_dd), drawdown_series


def max_drawdown_from_returns(returns: pd.Series) -> Tuple[float, pd.Series]:
    """Compute Max Drawdown starting from a daily-return series (base value 1.0)."""
    cumulative = (1 + returns).cumprod()
    return calculate_max_drawdown(cumulative)


# ------------------------------------------------------------------
# Beta
# ------------------------------------------------------------------

def calculate_beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Beta = Cov(asset, benchmark) / Var(benchmark).

    Aligns both series on common dates before computing. Returns np.nan
    if there is insufficient overlapping data or zero benchmark variance,
    so the caller can display a clear "unavailable" message instead of a
    fabricated number.
    """
    aligned = pd.concat([asset_returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(aligned) < 20:
        return np.nan

    asset_col, bench_col = aligned.columns[0], aligned.columns[1]
    covariance = aligned[asset_col].cov(aligned[bench_col])
    benchmark_variance = aligned[bench_col].var()

    if benchmark_variance == 0 or np.isnan(benchmark_variance):
        return np.nan

    return float(covariance / benchmark_variance)


def interpret_beta(beta: float) -> str:
    if np.isnan(beta):
        return "Beta unavailable due to insufficient or missing benchmark data."
    if beta > 1.05:
        return "Historically more sensitive to benchmark movements."
    if beta < -0.05:
        return "Historically moved inversely relative to the benchmark during the analyzed period."
    if beta < 0.95:
        return "Historically less sensitive to benchmark movements."
    return "Historically moved with similar sensitivity to the benchmark."


# ------------------------------------------------------------------
# Future value scenarios
# ------------------------------------------------------------------

def hypothetical_future_value(investment: float, annualized_return: float, years: float) -> float:
    """Future Value = Investment x (1 + Annualized Return) ^ Years."""
    return investment * ((1 + annualized_return) ** years)


# ------------------------------------------------------------------
# Extreme-return diagnostic
# ------------------------------------------------------------------

def extreme_return_diagnostics(returns: pd.Series, threshold: float = 0.15) -> Dict:
    """Flag unusually large daily moves that may indicate splits, bonus
    shares, or data-quality issues rather than genuine volatility."""
    if returns.empty:
        return {"max_return": None, "min_return": None, "extreme_detected": False}

    max_r = float(returns.max())
    min_r = float(returns.min())
    extreme = abs(max_r) > threshold or abs(min_r) > threshold
    return {"max_return": max_r, "min_return": min_r, "extreme_detected": extreme}


# ------------------------------------------------------------------
# Backtesting metrics
# ------------------------------------------------------------------

def train_test_split_returns(returns_df: pd.DataFrame, train_fraction: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological split — no shuffling, no lookahead. First `train_fraction`
    of observations = training/optimization period; remainder = out-of-sample
    test period."""
    split_idx = int(len(returns_df) * train_fraction)
    train = returns_df.iloc[:split_idx]
    test = returns_df.iloc[split_idx:]
    return train, test


def backtest_fixed_weights(test_returns_df: pd.DataFrame, weights: np.ndarray, investment: float) -> Dict:
    """
    Apply a fixed weight vector (derived from the TRAINING period only) to
    the out-of-sample TEST period and compute realized performance.
    """
    weighted_returns = test_returns_df @ weights
    cumulative = (1 + weighted_returns).cumprod() * investment

    total_return = float(cumulative.iloc[-1] / investment - 1) if len(cumulative) > 0 else 0.0
    n_days = len(weighted_returns)
    ann_return = float(weighted_returns.mean() * TRADING_DAYS_PER_YEAR) if n_days > 0 else 0.0
    ann_vol = float(weighted_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if n_days > 0 else 0.0
    max_dd, dd_series = calculate_max_drawdown(cumulative) if n_days > 0 else (0.0, pd.Series(dtype=float))

    return {
        "cumulative_value": cumulative,
        "total_return": total_return,
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_dd,
        "drawdown_series": dd_series,
        "final_value": float(cumulative.iloc[-1]) if n_days > 0 else investment,
        "sharpe_ratio": portfolio_sharpe_ratio(ann_return, ann_vol, 0.0),
    }


def build_stock_analytics_table(
    price_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    risk_free_rate: float,
    benchmark_returns: pd.Series,
    investment: float,
) -> pd.DataFrame:
    """Assemble the full per-stock analytics table used throughout the dashboard."""
    rows = []
    ann_ret = expected_annual_return(returns_df)
    ann_vol = annual_volatility(returns_df)
    sharpe = sharpe_ratios(returns_df, risk_free_rate)

    for symbol in returns_df.columns:
        beta = calculate_beta(returns_df[symbol], benchmark_returns) if not benchmark_returns.empty else np.nan
        max_dd, _ = max_drawdown_from_returns(returns_df[symbol])
        fv_1y = hypothetical_future_value(investment, ann_ret[symbol], 1)
        fv_5y = hypothetical_future_value(investment, ann_ret[symbol], 5)

        rows.append({
            "Symbol": symbol,
            "Avg Daily Return": average_daily_return(returns_df)[symbol],
            "Daily Volatility": daily_volatility(returns_df)[symbol],
            "Expected Annual Return": ann_ret[symbol],
            "Annual Volatility": ann_vol[symbol],
            "Sharpe Ratio": sharpe[symbol],
            "Beta": beta,
            "Max Drawdown": max_dd,
            "1-Year Hypothetical Value": fv_1y,
            "5-Year Hypothetical Value": fv_5y,
        })

    return pd.DataFrame(rows).set_index("Symbol")
