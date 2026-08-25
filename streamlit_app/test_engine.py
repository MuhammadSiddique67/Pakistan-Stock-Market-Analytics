"""
test_engine.py

Standalone smoke test for the core backend engine (data_fetcher, analytics,
portfolio_optimizer). Run directly with:

    python test_engine.py

Uses the LOCAL CSV dataset — no internet connection required.
"""

import sys
import numpy as np

from data_fetcher import fetch_multiple_stocks, build_synthetic_benchmark, load_stock_database, dataset_date_range
import analytics as an
import portfolio_optimizer as opt


def run_tests():
    print("=" * 60)
    print("PSX PORTFOLIO OPTIMIZER - CORE ENGINE TEST (offline / CSV)")
    print("=" * 60)

    test_symbols = ["MEBL", "OGDC", "FFC", "LUCK", "MCB"]
    start_date = "2021-01-01"
    end_date = "2025-12-31"
    risk_free_rate = 0.10

    print("\n[1] Loading stock database...")
    db = load_stock_database()
    assert not db.empty, "Stock database failed to load"
    print(f"    Loaded {len(db)} companies across {db['sector'].nunique()} sectors.")

    print("\n[2] Checking dataset date range...")
    dmin, dmax = dataset_date_range()
    print(f"    Dataset spans {dmin.date()} to {dmax.date()}")

    print("\n[3] Loading historical price data from CSV...")
    price_df, quality_report, failed = fetch_multiple_stocks(test_symbols, start_date, end_date)
    assert not price_df.empty, "Price data load failed"
    print(f"    Loaded {len(price_df.columns)} stocks, {len(price_df)} common trading days.")
    if failed:
        print(f"    WARNING - failed symbols: {failed}")

    print("\n[4] Calculating returns and risk metrics...")
    returns_df = an.calculate_daily_returns(price_df)
    ann_ret = an.expected_annual_return(returns_df)
    ann_vol = an.annual_volatility(returns_df)
    cov_matrix = an.annualized_covariance_matrix(returns_df)
    sharpe = an.sharpe_ratios(returns_df, risk_free_rate)
    print(f"    Annualized returns:\n{ann_ret}")
    print(f"    Sharpe ratios:\n{sharpe}")

    print("\n[5] Running Maximum Sharpe optimization...")
    max_sharpe_result = opt.optimize_max_sharpe(ann_ret, cov_matrix, risk_free_rate)
    assert abs(max_sharpe_result["weights"].sum() - 1.0) < 1e-4, "Weights do not sum to 1"
    assert (max_sharpe_result["weights"] >= -1e-6).all(), "Negative weight detected (short selling)"
    print(f"    Max Sharpe weights:\n{max_sharpe_result['weights']}")
    print(f"    Portfolio Sharpe Ratio: {max_sharpe_result['sharpe_ratio']:.4f}")

    print("\n[6] Running Minimum Volatility optimization...")
    min_vol_result = opt.optimize_min_volatility(ann_ret, cov_matrix)
    assert abs(min_vol_result["weights"].sum() - 1.0) < 1e-4, "Weights do not sum to 1"
    print(f"    Min Vol weights:\n{min_vol_result['weights']}")

    print("\n[7] Calculating efficient frontier (10 sample points)...")
    frontier = opt.calculate_efficient_frontier(ann_ret, cov_matrix, n_points=10)
    assert not frontier.empty, "Efficient frontier calculation returned no points"
    print(f"    Frontier points calculated: {len(frontier)}")

    print("\n[8] Running Monte Carlo simulation (500 portfolios, fast test size)...")
    sim = opt.monte_carlo_simulation(ann_ret, cov_matrix, risk_free_rate, n_portfolios=500)
    assert len(sim) == 500, "Monte Carlo simulation returned unexpected portfolio count"
    print(f"    Simulated Sharpe range: {sim['sharpe_ratio'].min():.3f} to {sim['sharpe_ratio'].max():.3f}")

    print("\n[9] Calculating Maximum Drawdown...")
    for symbol in returns_df.columns:
        max_dd, _ = an.max_drawdown_from_returns(returns_df[symbol])
        print(f"    {symbol}: {max_dd:.2%}")

    print("\n[10] Building synthetic benchmark and calculating Beta...")
    benchmark_data = build_synthetic_benchmark(start_date, end_date)
    assert not benchmark_data.empty, "Synthetic benchmark construction failed"
    benchmark_returns = benchmark_data["Close"].pct_change().dropna()
    for symbol in returns_df.columns:
        beta = an.calculate_beta(returns_df[symbol], benchmark_returns)
        print(f"    {symbol} Beta: {beta if np.isnan(beta) else round(beta, 3)}")

    print("\n[11] Running historical backtest (70/30 split)...")
    train_returns, test_returns = an.train_test_split_returns(returns_df, 0.7)
    train_ann_ret = an.expected_annual_return(train_returns)
    train_cov = an.annualized_covariance_matrix(train_returns)
    train_weights = opt.optimize_max_sharpe(train_ann_ret, train_cov, risk_free_rate)["weights"]
    backtest_result = an.backtest_fixed_weights(test_returns, train_weights.values, 100000)
    print(f"    Backtest total return: {backtest_result['total_return']:.2%}")
    print(f"    Backtest final value: PKR {backtest_result['final_value']:,.2f}")

    print("\n" + "=" * 60)
    print("ALL CORE ENGINE TESTS PASSED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\nTEST FAILED (assertion): {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nTEST FAILED (error): {e}")
        sys.exit(1)
