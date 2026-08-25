"""
data_fetcher.py

Loads, validates, and aligns historical PSX stock price data from the
LOCAL master CSV file (PSX_2015_2025_Master_Data.csv) instead of any
live network source. No internet connection is required or used.

Expected CSV format (long/tidy):
    Date, Symbol, Open, High, Low, Close, Adj Close, Volume

No fake or hard-coded financial data is used anywhere in this module —
every number returned comes directly from the CSV.
"""

import pandas as pd
import numpy as np
import streamlit as st
import os
from typing import Dict, List, Tuple

MASTER_DATA_FILENAME = "PSX_2015_2025_Master_Data.csv"
STOCK_DB_FILENAME = "stock_database.csv"


def _resolve_path(filename: str) -> str:
    """Look for the data file next to this script first, then in the
    current working directory — keeps the app portable across machines."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, filename)
    if os.path.exists(candidate):
        return candidate
    return filename


@st.cache_data(show_spinner=False)
def load_master_dataset() -> pd.DataFrame:
    """
    Load the full local historical dataset once (cached for the session).
    Returns the raw long-format DataFrame with a proper DatetimeIndex-ready
    'Date' column.
    """
    path = _resolve_path(MASTER_DATA_FILENAME)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"'{MASTER_DATA_FILENAME}' was not found. Place it in the same folder as app.py."
        )
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.sort_values(["Symbol", "Date"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def available_symbols() -> List[str]:
    df = load_master_dataset()
    return sorted(df["Symbol"].unique().tolist())


@st.cache_data(show_spinner=False)
def dataset_date_range() -> Tuple[pd.Timestamp, pd.Timestamp]:
    df = load_master_dataset()
    return df["Date"].min(), df["Date"].max()


def validate_stock_data(symbol: str, symbol_df: pd.DataFrame, requested_start, requested_end) -> Dict:
    """Run data-quality checks on a single stock's slice of the dataset."""
    warnings = []
    n_obs = len(symbol_df)

    if n_obs == 0:
        warnings.append("No observations available in the requested date range.")
        return {
            "symbol": symbol, "n_observations": 0, "missing_values": 0,
            "first_date": None, "last_date": None, "warnings": warnings,
        }

    missing = int(symbol_df["Close"].isna().sum())
    if n_obs < 60:
        warnings.append(
            f"Only {n_obs} trading days of data available in this range. "
            f"Annualized statistics may be unreliable with such a short history."
        )
    if missing > 0:
        warnings.append(f"{missing} missing closing price values detected.")

    actual_first = symbol_df["Date"].min()
    actual_last = symbol_df["Date"].max()
    if pd.Timestamp(requested_start) < actual_first:
        warnings.append(f"Data only starts on {actual_first.date()} — earlier than the requested start date.")
    if pd.Timestamp(requested_end) > actual_last:
        warnings.append(f"Data only extends to {actual_last.date()} — earlier than the requested end date.")

    returns = symbol_df["Close"].pct_change().dropna()
    if not returns.empty:
        max_ret, min_ret = returns.max(), returns.min()
        if abs(max_ret) > 0.15 or abs(min_ret) > 0.15:
            warnings.append(
                "Unusually large historical daily returns were detected. These may reflect genuine "
                "market movements, corporate actions, stock splits, bonus-share adjustments, illiquidity, "
                "or data-quality issues. Review the observations before interpreting volatility."
            )

    return {
        "symbol": symbol, "n_observations": n_obs, "missing_values": missing,
        "first_date": actual_first, "last_date": actual_last, "warnings": warnings,
    }


def fetch_multiple_stocks(
    symbols: List[str], start_date: str, end_date: str
) -> Tuple[pd.DataFrame, Dict[str, Dict], List[str]]:
    """
    Slice historical closing prices for multiple PSX stocks from the local
    dataset and align them on common trading dates.

    Returns:
        price_df: DataFrame of aligned Close prices, columns = symbols.
        quality_report: dict of {symbol: validation dict}.
        failed_symbols: symbols with zero observations in range.
    """
    master = load_master_dataset()
    start_ts, end_ts = pd.Timestamp(start_date), pd.Timestamp(end_date)

    price_series = {}
    quality_report = {}
    failed_symbols = []

    for symbol in symbols:
        sym_df = master[(master["Symbol"] == symbol) & (master["Date"] >= start_ts) & (master["Date"] <= end_ts)]
        report = validate_stock_data(symbol, sym_df, start_ts, end_ts)
        quality_report[symbol] = report

        if report["n_observations"] == 0:
            failed_symbols.append(symbol)
            continue

        price_series[symbol] = sym_df.set_index("Date")["Close"]

    if not price_series:
        return pd.DataFrame(), quality_report, failed_symbols

    price_df = pd.DataFrame(price_series)
    aligned_df = price_df.dropna(how="any")

    if aligned_df.empty:
        aligned_df = price_df.ffill().dropna(how="any")

    if not aligned_df.empty:
        for symbol in aligned_df.columns:
            quality_report[symbol]["common_start_date"] = aligned_df.index.min()
            quality_report[symbol]["common_end_date"] = aligned_df.index.max()
            quality_report[symbol]["common_observations"] = len(aligned_df)

    return aligned_df, quality_report, failed_symbols


@st.cache_data(show_spinner=False)
def build_synthetic_benchmark(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Build a proxy market benchmark as the equal-weighted average daily
    return across every stock in the local dataset for the given period.

    This is NOT the official KSE-100 index — the master CSV does not
    include index-level data. It is clearly labeled as a synthetic,
    dataset-derived proxy wherever it is shown in the app, so Beta values
    are never presented as if benchmarked against the real KSE-100.
    """
    master = load_master_dataset()
    start_ts, end_ts = pd.Timestamp(start_date), pd.Timestamp(end_date)
    window = master[(master["Date"] >= start_ts) & (master["Date"] <= end_ts)]

    if window.empty:
        return pd.DataFrame()

    wide = window.pivot(index="Date", columns="Symbol", values="Close").sort_index()
    daily_returns = wide.pct_change()
    equal_weight_return = daily_returns.mean(axis=1, skipna=True).dropna()

    if equal_weight_return.empty:
        return pd.DataFrame()

    synthetic_close = (1 + equal_weight_return).cumprod() * 100.0
    return pd.DataFrame({"Close": synthetic_close})


def load_stock_database(csv_path: str = None) -> pd.DataFrame:
    """Load the local PSX stock/sector reference database used for the
    asset-selection UI (search by name, ticker, or sector). Restricted to
    exactly the symbols present in the master historical dataset."""
    path = _resolve_path(csv_path or STOCK_DB_FILENAME)
    try:
        db = pd.read_csv(path)
    except FileNotFoundError:
        raise ValueError(
            f"'{STOCK_DB_FILENAME}' not found at '{path}'. This file is required for "
            f"sector-based and name-based stock search."
        )
    valid_symbols = set(available_symbols())
    return db[db["symbol"].isin(valid_symbols)].reset_index(drop=True)
