# PSX Portfolio Optimizer & Financial Analytics Dashboard

An interactive Streamlit application for exploring the historical risk-return
characteristics of Pakistan Stock Exchange (PSX) stocks and building
mathematically optimized portfolios using Modern Portfolio Theory.

**Data source:** 100% local — `PSX_2015_2025_Master_Data.csv` (99 PSX stocks,
2015–2025 daily prices). No internet connection or live API calls are used.

## Features

- Two-page flow: **Selection page** (pick stocks, investment, strategy) → **Dashboard page** (full analytics)
- Dynamic stock selection: search by name/ticker, or browse by sector (17 real PSX sectors)
- Maximum Sharpe Ratio, Minimum Volatility, or **Compare Both** side by side
- Exact constrained Efficient Frontier + 6,000-portfolio Monte Carlo simulation
- Individual stock analytics: return, volatility, Sharpe, Beta, Max Drawdown
- Correlation heatmap & annualized covariance matrix
- Historical backtesting with chronological train/test split (no lookahead)
- Automated plain-language summary of results
- CSV export of allocation, comparison, and summary data
- Dark navy / purple "fintech" themed dashboard, including native dark-themed tables

## Project Structure

```
PSX-Portfolio-Optimizer/
├── app.py                          # Main Streamlit app (2-page flow)
├── data_fetcher.py                 # Loads & validates data from the local CSV
├── analytics.py                    # Returns, volatility, Sharpe, Beta, drawdown, backtest math
├── portfolio_optimizer.py          # SLSQP optimization, efficient frontier, Monte Carlo
├── visualization.py                # Plotly chart builders
├── stock_database.csv              # Symbol / company name / sector reference (99 rows)
├── PSX_2015_2025_Master_Data.csv   # Historical price dataset (REQUIRED — must sit next to app.py)
├── test_engine.py                  # Offline backend smoke test
├── requirements.txt
├── .streamlit/config.toml          # Dark theme (fixes native table/dataframe styling)
├── .gitignore
```

## Setup

```bash
pip install -r requirements.txt
```

**Important:** `PSX_2015_2025_Master_Data.csv` must be in the same folder as `app.py`.
It's ~27 MB — well within GitHub's and Streamlit Community Cloud's limits.

## Run the backend test (fully offline)

```bash
python test_engine.py
```

## Run the dashboard

```bash
python -m streamlit run app.py
```

## Known data quality note

8 of the 99 symbols in the dataset (**LUCK, SYS, ICI, KOHC, KTML, THCCL, UBL, MARI**)
contain at least one single-day price move greater than 50%, which is almost
certainly a data error in the source file rather than a real market move (e.g.
LUCK shows an unexplained -80% then +396% within days — not a real split
pattern). This is **not** something the app silently fixes — per the project's
"no fake data" rule, these are surfaced as warnings in the **Analytics → Data
Quality & Validation** section instead. If you're presenting this for your FYP,
it's worth mentioning as a known dataset limitation, or excluding those symbols
from your demo portfolio if you want cleaner numbers.

## Methodology Notes

- Trading year assumed as 252 days.
- Expected Annual Return = Mean Daily Return × 252.
- Annual Volatility = Std Dev of Daily Returns × √252.
- Sharpe Ratio = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility.
- Long-only, fully-invested portfolios (weights sum to 1, no short selling).
- **Beta uses a synthetic equal-weighted benchmark** built from all 99 stocks
  in the dataset — the CSV does not include the official KSE-100 index, so
  Beta is a relative-sensitivity estimate against this basket, not the real
  index. This is labeled clearly in the app (About and Analytics pages).
- Backtesting uses a chronological 70/30 train/test split — weights are
  computed on the training period only and applied unchanged to the
  out-of-sample test period.

## Disclaimer

This application is intended for educational and analytical purposes only
and does not constitute financial, investment, legal, or tax advice.
Results are based on historical market data and mathematical models.
Historical performance does not guarantee future results.
