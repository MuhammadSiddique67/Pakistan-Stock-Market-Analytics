"""
app.py

PSX Portfolio Optimizer & Financial Analytics Dashboard
Main Streamlit application. Data source: local CSV (PSX_2015_2025_Master_Data.csv)
— no live network fetching.

Two-page flow:
  Page 1 (view="setup")   -> stock selection, investment settings, strategy choice
  Page 2 (view="results") -> full dashboard with sidebar navigation

Run with:  python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

import data_fetcher as df_mod
import analytics as an
import portfolio_optimizer as opt
import visualization as viz

# ------------------------------------------------------------------
# Page config & custom CSS
# ------------------------------------------------------------------

st.set_page_config(
    page_title="PSX Portfolio Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Move whole page content upward */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 0.5rem !important;
}

/* Make hero/title more compact */
.setup-hero {
    padding: 0px 0 8px 0 !important;
}

.setup-hero h1 {
    margin-top: 0 !important;
    margin-bottom: 2px !important;
}

.setup-hero p {
    margin-top: 0 !important;
    margin-bottom: 8px !important;
}

/* Reduce spacing around section headings */
.section-header {
    margin-top: 8px !important;
    margin-bottom: 4px !important;
}

/* Reduce vertical gaps between Streamlit widgets */
div[data-testid="stVerticalBlock"] {
    gap: 1rem !important;
}

/* Make strategy information box compact */
.info-box {
    padding: 8px 12px !important;
    margin-bottom: 5px !important;
}

/* Make disclaimer compact */
.disclaimer-box {
    padding: 8px 12px !important;
    margin-top: 8px !important;
}
.stApp {
    background: linear-gradient(180deg, #0b0e24 0%, #0f1229 100%);
    color: #e5e7f5;
}
section[data-testid="stSidebar"] {
    background-color: #10132c;
    border-right: 1px solid #2a2f52;
}
.kpi-card {
    background: linear-gradient(145deg, #171b3a 0%, #1d2148 100%);
    border: 1px solid #2a2f52;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 4px 18px rgba(139, 92, 246, 0.08);
    margin-bottom: 10px;
}
.kpi-label { color: #9ca3d4; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.kpi-value { color: #f4f4fb; font-size: 1.55rem; font-weight: 700; }
.kpi-sub { color: #a78bfa; font-size: 0.8rem; margin-top: 2px; }
.section-header {
    color: #f4f4fb; font-size: 1.3rem; font-weight: 700;
    margin-top: 18px; margin-bottom: 6px;
    border-left: 4px solid #8b5cf6; padding-left: 12px;
}
.info-box {
    background: #171b3a; border: 1px solid #2a2f52; border-left: 4px solid #a78bfa;
    border-radius: 10px; padding: 14px 18px; color: #cfd2ec; font-size: 0.92rem; margin-bottom: 14px;
}
.disclaimer-box {
    background: #1d1230; border: 1px solid #3b2a5e; border-radius: 10px;
    padding: 14px 18px; color: #c9b8ec; font-size: 0.82rem; margin-top: 20px;
}
.setup-hero {
    text-align: center; padding: 10px 0 20px 0;
}
.setup-hero h1 { color: #f4f4fb; font-size: 2.1rem; margin-bottom: 4px; }
.setup-hero p { color: #9ca3d4; font-size: 1rem; }
.stepper-badge {
    display: inline-block; background: #8b5cf6; color: white; border-radius: 50%;
    width: 26px; height: 26px; text-align: center; line-height: 26px; font-weight: 700; margin-right: 8px;
}

/* ---- Dark theme fix for Streamlit's native dataframe / table grid ---- */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    background-color: #171b3a !important;
    border: 1px solid #2a2f52 !important;
    border-radius: 10px !important;
}
div[data-testid="stDataFrame"] * , div[data-testid="stTable"] * {
    color: #e5e7f5 !important;
}
div[data-testid="stMetric"] {
    background-color: #171b3a; border: 1px solid #2a2f52; border-radius: 12px; padding: 10px;
}

/* Make Streamlit input labels and radio text white */
div[data-testid="stNumberInput"] label,
div[data-testid="stSlider"] label,
div[data-testid="stRadio"] label,
div[data-testid="stSelectbox"] label {
    color: #ffffff !important;
}

div[data-testid="stRadio"] p {
    color: #ffffff !important;
}

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

RISK_FREE_DEFAULT = 0.10

# ------------------------------------------------------------------
# Session state init
# ------------------------------------------------------------------

defaults = {
    "view": "setup",
    "results": None,
    "selected_symbols": ["MEBL", "OGDC", "FFC", "LUCK", "MCB"],
    "active_view_strategy": "Maximum Sharpe Ratio",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def kpi_card(label, value, sub=None, icon="📊", icon_color="#8b5cf6"):
    st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
</div>
""", unsafe_allow_html=True)
    
def fmt_pkr(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "N/A"
    return f"Rs. {x:,.0f}"


def fmt_pct(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "N/A"
    return f"{x*100:.2f}%"


def fmt_num(x, dp=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "N/A"
    return f"{x:.{dp}f}"


# ------------------------------------------------------------------
# Load reference data (local, no network)
# ------------------------------------------------------------------

try:
    stock_db = df_mod.load_stock_database()
    dataset_min_date, dataset_max_date = df_mod.dataset_date_range()
except (ValueError, FileNotFoundError) as e:
    st.error(str(e))
    st.stop()

symbol_to_name = dict(zip(stock_db["symbol"], stock_db["company_name"]))
symbol_to_sector = dict(zip(stock_db["symbol"], stock_db["sector"]))

DATASET_MIN = dataset_min_date.date()
DATASET_MAX = dataset_max_date.date()


# ------------------------------------------------------------------
# Strategy package builder (shared by Max Sharpe / Min Vol so both are
# always fully computed — needed for "Compare Both" mode)
# ------------------------------------------------------------------

def compute_strategy_package(opt_result, returns_df, benchmark_returns, investment_amount, risk_free_rate):
    weights_aligned = opt_result["weights"].reindex(returns_df.columns).fillna(0).values
    port_daily_returns = returns_df @ weights_aligned

    sharpe = opt_result.get("sharpe_ratio")
    if sharpe is None:
        sharpe = an.portfolio_sharpe_ratio(opt_result["expected_return"], opt_result["volatility"], risk_free_rate)

    beta = np.nan
    if not benchmark_returns.empty:
        beta = an.calculate_beta(port_daily_returns, benchmark_returns)

    cum_value = (1 + port_daily_returns).cumprod() * investment_amount
    max_dd, dd_series = an.calculate_max_drawdown(cum_value)

    fv_1y = an.hypothetical_future_value(investment_amount, opt_result["expected_return"], 1)
    fv_5y = an.hypothetical_future_value(investment_amount, opt_result["expected_return"], 5)

    return {
        "weights": opt_result["weights"],
        "expected_return": opt_result["expected_return"],
        "volatility": opt_result["volatility"],
        "sharpe_ratio": sharpe,
        "beta": beta,
        "max_drawdown": max_dd,
        "drawdown_series": dd_series,
        "cumulative_value": cum_value,
        "fv_1y": fv_1y,
        "fv_5y": fv_5y,
    }


# ------------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------------

def run_pipeline(picked_symbols, investment_amount, start_date, end_date, risk_free_rate, strategy_mode):
    if len(picked_symbols) < 2:
        st.error("Please select at least 2 stocks (up to 25).")
        return None
    if len(picked_symbols) > 25:
        st.error("Please select no more than 25 stocks.")
        return None

    with st.spinner("Loading historical market data..."):
        price_df, quality_report, failed = df_mod.fetch_multiple_stocks(
            picked_symbols, str(start_date), str(end_date)
        )

    if failed:
        st.warning(f"The following symbols had no data in this range and were excluded: {', '.join(failed)}")

    if price_df.empty or len(price_df.columns) < 2:
        st.error("Insufficient historical data to build a portfolio. Try different stocks or a wider date range.")
        return None

    with st.spinner("Calculating analytics..."):
        returns_df = an.calculate_daily_returns(price_df)
        ann_ret = an.expected_annual_return(returns_df)
        ann_vol = an.annual_volatility(returns_df)
        cov_matrix = an.annualized_covariance_matrix(returns_df)
        corr_matrix = an.correlation_matrix(returns_df)

    with st.spinner("Building market benchmark proxy..."):
        benchmark_data = df_mod.build_synthetic_benchmark(str(start_date), str(end_date))
        benchmark_returns = (
            benchmark_data["Close"].pct_change().dropna() if not benchmark_data.empty else pd.Series(dtype=float)
        )

    with st.spinner("Optimizing portfolio..."):
        try:
            max_sharpe = opt.optimize_max_sharpe(ann_ret, cov_matrix, risk_free_rate)
            min_vol = opt.optimize_min_volatility(ann_ret, cov_matrix)
        except ValueError as e:
            st.error(f"Optimization failed: {e}")
            return None

    with st.spinner("Simulating portfolios for the Efficient Frontier..."):
        sim_df = opt.monte_carlo_simulation(ann_ret, cov_matrix, risk_free_rate, n_portfolios=6000)
        frontier_df = opt.calculate_efficient_frontier(ann_ret, cov_matrix, n_points=40)

    with st.spinner("Generating analytics dashboard..."):
        stock_table = an.build_stock_analytics_table(price_df, returns_df, risk_free_rate, benchmark_returns, investment_amount)

        packages = {
            "Maximum Sharpe Ratio": compute_strategy_package(max_sharpe, returns_df, benchmark_returns, investment_amount, risk_free_rate),
            "Minimum Volatility": compute_strategy_package(min_vol, returns_df, benchmark_returns, investment_amount, risk_free_rate),
        }

        train_returns, test_returns = an.train_test_split_returns(returns_df, 0.7)
        train_ann_ret = an.expected_annual_return(train_returns)
        train_cov = an.annualized_covariance_matrix(train_returns)

        backtest_results = {}
        try:
            bt_max_sharpe_w = opt.optimize_max_sharpe(train_ann_ret, train_cov, risk_free_rate)["weights"]
            backtest_results["Maximum Sharpe"] = an.backtest_fixed_weights(test_returns, bt_max_sharpe_w.reindex(test_returns.columns).values, investment_amount)
        except ValueError:
            pass
        try:
            bt_min_vol_w = opt.optimize_min_volatility(train_ann_ret, train_cov)["weights"]
            backtest_results["Minimum Volatility"] = an.backtest_fixed_weights(test_returns, bt_min_vol_w.reindex(test_returns.columns).values, investment_amount)
        except ValueError:
            pass
        eq_weights = np.repeat(1 / len(test_returns.columns), len(test_returns.columns))
        backtest_results["Equal-Weight"] = an.backtest_fixed_weights(test_returns, eq_weights, investment_amount)

    return {
        "price_df": price_df, "returns_df": returns_df, "quality_report": quality_report,
        "ann_ret": ann_ret, "ann_vol": ann_vol, "cov_matrix": cov_matrix, "corr_matrix": corr_matrix,
        "max_sharpe": max_sharpe, "min_vol": min_vol, "packages": packages,
        "sim_df": sim_df, "frontier_df": frontier_df, "stock_table": stock_table,
        "backtest_results": backtest_results, "benchmark_returns": benchmark_returns,
        "investment_amount": investment_amount, "strategy_mode": strategy_mode,
        "picked_symbols": list(price_df.columns), "start_date": start_date, "end_date": end_date,
    }


# ==================================================================
# PAGE 1 — SETUP / SELECTION
# ==================================================================

def render_setup_page():
    st.markdown(
        '<div class="setup-hero"><h1>📊 PSX Portfolio Optimizer</h1>'
        '<p>Build a data-driven, optimized portfolio from real historical PSX prices (2015–2025)</p></div>',
        unsafe_allow_html=True,
    )

    # Persistent selection state
    if "selected_symbols" not in st.session_state:
        st.session_state.selected_symbols = []

    col1, col2 = st.columns([1.1, 1])

    # =========================================================
    # right COLUMN — SELECT ASSETS
    # =========================================================
    with col2:
        st.markdown(
            '<div class="section-header">'
            '<span class="stepper-badge">2</span>Select Assets'
            '</div>',
            unsafe_allow_html=True,
        )

        # Sector -> Stock dropdowns
        sectors = sorted(stock_db["sector"].dropna().unique())
        chosen_sector = st.selectbox("Select Sector", sectors, key="chosen_sector")

        sector_stocks = stock_db[stock_db["sector"] == chosen_sector]
        stock_options = [
            f"{r.symbol} — {r.company_name}" for r in sector_stocks.itertuples()
        ]

        selected_stock = st.selectbox(
            "Select Stock",
            ["Choose Stock"] + stock_options,
            key="stock_picker",
        )

        # Add Stock
        if st.button("➕ Add Stock", key="add_stock_button", use_container_width=True):
            if selected_stock == "Choose Stock":
                st.warning("Please select a stock first.")
            else:
                symbol = selected_stock.split(" — ")[0]
                if symbol in st.session_state.selected_symbols:
                    st.warning(f"{symbol} is already selected.")
                elif len(st.session_state.selected_symbols) >= 25:
                    st.warning("Maximum of 25 stocks allowed.")
                else:
                    st.session_state.selected_symbols.append(symbol)
                    st.rerun()

        # Selected Stocks — manual render (NOT st.multiselect, so it can't
        # overwrite st.session_state.selected_symbols on its own)
        st.markdown("### Selected Stocks")

        if st.session_state.selected_symbols:
            cols = st.columns(len(st.session_state.selected_symbols))

            for i, symbol in enumerate(st.session_state.selected_symbols.copy()):
                with cols[i]:
                    if st.button(
                        f"{symbol}  ✕",
                        key=f"remove_{symbol}",
                        use_container_width=True
                 ):
                        st.session_state.selected_symbols.remove(symbol)
                        st.rerun()
        else:
            st.info("No stocks selected yet.")

        picked_symbols = st.session_state.selected_symbols.copy()

        st.caption(
            f"Selected: {len(picked_symbols)} stock(s). Choose between 2 and 25 stocks."
        )

    # =========================================================
    # RIGHT COLUMN — INVESTMENT SETTINGS & STRATEGY
    # =========================================================
    with col2:
        # -----------------------------------------------------------
        # NOT INCLUDED IN YOUR PASTE — placeholder only.
        # Your real col2 code (Total Investment, Risk-Free Rate,
        # strategy selection, strategy info boxes, Optimize Portfolio
        # button, disclaimer) never appeared in the snippet you sent —
        # only col1 was there. Paste it back in and delete this block.
        #
        # When you wire up the Optimize button, call run_pipeline()
        # with dataset bounds instead of any date widgets:
        #
        #   results = run_pipeline(
        #       symbols=picked_symbols,
        #       start_date=DATASET_MIN,
        #       end_date=DATASET_MAX,
        #       ...  # your existing investment / risk-free-rate / strategy args
        #   )
        #
        # Also worth adding there: block/validate Optimize if
        # len(picked_symbols) < 2 — that's not enforced anywhere yet.
        # -----------------------------------------------------------
        pass

    # =========================================================
    # RIGHT COLUMN — INVESTMENT SETTINGS
    # =========================================================
    with col1:

        st.markdown(
            '<div class="section-header">'
            '<span class="stepper-badge">1</span>'
            'Investment Amount'
            '</div>',
            unsafe_allow_html=True,
        )

        # Investment Amount
        investment_amount = st.number_input(
            "Total Investment (PKR)",
            min_value=1000,
            value=150000,
            step=5000,
            key="investment_amount",
        )

        # Risk-Free Rate
        risk_free_rate = st.slider(
            "Risk-Free Rate (annual)",
            min_value=0.0,
            max_value=0.30,
            value=RISK_FREE_DEFAULT,
            step=0.005,
            format="%.3f",
            key="risk_free_rate",
        )

        # =====================================================
        # STRATEGY
        # =====================================================

        st.markdown(
            '<div class="section-header">'
            '<span class="stepper-badge">3</span>'
            'Strategy'
            '</div>',
            unsafe_allow_html=True,
        )

        strategy_mode = st.radio(
            "Optimization Strategy",
            [
                "Maximum Sharpe Ratio",
                "Minimum Volatility",
                "Compare Both",
            ],
            key="strategy_mode",
        )

        # Strategy Description
        if strategy_mode == "Maximum Sharpe Ratio":

            st.markdown(
                '<div class="info-box">'
                'Seeks the highest estimated '
                '<b>risk-adjusted</b> return — balances '
                'expected return against volatility rather '
                'than simply maximizing return.'
                '</div>',
                unsafe_allow_html=True,
            )

        elif strategy_mode == "Minimum Volatility":

            st.markdown(
                '<div class="info-box">'
                'Seeks the portfolio with the '
                '<b>lowest historical volatility</b> '
                'among the selected assets, regardless '
                'of expected return.'
                '</div>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                '<div class="info-box">'
                'Calculates <b>both</b> strategies so you '
                'can compare them side by side on the '
                'dashboard and switch between them freely.'
                '</div>',
                unsafe_allow_html=True,
            )

    # =========================================================
    # OPTIMIZE BUTTON
    # =========================================================

    st.markdown("---")

    _, mid, _ = st.columns([1, 1, 1])

    with mid:

        run_button = st.button(
            "🚀 Optimize Portfolio",
            use_container_width=True,
            type="primary",
        )

    # =========================================================
    # RUN PORTFOLIO OPTIMIZATION
    # =========================================================

    if run_button:

        # Minimum stock validation
        if len(picked_symbols) < 2:

            st.error(
                "Please select at least 2 stocks "
                "before optimizing your portfolio."
            )

        else:

            result = run_pipeline(
                picked_symbols,
                investment_amount,
                DATASET_MIN,
                DATASET_MAX,
                risk_free_rate,
                strategy_mode,
            )

            if result:

                st.session_state.results = result

                st.session_state.active_view_strategy = (
                    "Maximum Sharpe Ratio"
                    if strategy_mode != "Minimum Volatility"
                    else "Minimum Volatility"
                )

                st.session_state.view = "results"

                st.rerun()

    # =========================================================
    # DISCLAIMER
    # =========================================================

    st.markdown(
        '<div class="disclaimer-box">'
        'This application is intended for educational and '
        'analytical purposes only and does not constitute '
        'financial, investment, legal, or tax advice. '
        'Results are based on historical market data and '
        'mathematical models. Historical performance does '
        'not guarantee future results.'
        '</div>',
        unsafe_allow_html=True,
    )

# ==================================================================
# PAGE 2 — RESULTS DASHBOARD
# ==================================================================

def render_results_page():
    R = st.session_state.results

    st.sidebar.markdown("## 📊 PSX Portfolio Optimizer")
    st.sidebar.caption("Educational financial analytics — not investment advice.")
    if st.sidebar.button("← Back to Selection", use_container_width=True):
        st.session_state.view = "setup"
        st.rerun()

    st.sidebar.markdown("---")
    nav_section = st.sidebar.radio(
        "Navigate", ["Dashboard", "Asset Selection", "Backtesting", "Analytics", "Reports", "About"], key="nav_section"
    )
    st.sidebar.markdown("---")
    st.sidebar.caption(f"**Stocks:** {len(R['picked_symbols'])}")
    st.sidebar.caption(f"**Investment:** {fmt_pkr(R['investment_amount'])}")
    st.sidebar.caption(f"**Period:** {R['start_date']} to {R['end_date']}")
    st.sidebar.caption(f"**Mode:** {R['strategy_mode']}")

    # Strategy selector — always available so the person can flip between
    # Max Sharpe / Min Vol regardless of what was chosen on the setup page.
    active_label = st.sidebar.radio(
        "Viewing strategy", ["Maximum Sharpe Ratio", "Minimum Volatility"],
        key="active_view_strategy",
    )
    active = R["packages"][active_label]

    if nav_section == "About":
        render_about()
        return
    if nav_section == "Asset Selection":
        render_asset_selection(R)
        return
    if nav_section == "Dashboard":
        render_dashboard(R, active, active_label)
        return
    if nav_section == "Backtesting":
        render_backtesting(R)
        return
    if nav_section == "Analytics":
        render_analytics(R)
        return
    if nav_section == "Reports":
        render_reports(R, active, active_label)
        return


def render_about():
    st.markdown('<div class="section-header">About This Application</div>', unsafe_allow_html=True)
    st.write(
        "The PSX Portfolio Optimizer is an educational tool for exploring the historical risk-return "
        "characteristics of Pakistan Stock Exchange stocks and comparing them against mathematically "
        "optimized portfolios (Modern Portfolio Theory / Markowitz framework). All calculations use "
        "real historical data (2015–2025) loaded from a local dataset — no live network calls are made."
    )
    st.markdown(
        '<div class="info-box">The Beta values shown elsewhere in this app use a <b>synthetic equal-weighted '
        'benchmark</b> built from every stock in this dataset — not the official KSE-100 index, which is not '
        'included in the dataset. Treat Beta as a relative-sensitivity estimate versus this basket, not the '
        'live market index.</div>', unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="disclaimer-box">This application is intended for educational and analytical purposes only '
        'and does not constitute financial, investment, legal, or tax advice. Results are based on historical '
        'market data and mathematical models. Historical performance does not guarantee future results. Expected '
        'returns, risk estimates, optimized allocations, backtesting results, and hypothetical future values may '
        'differ materially from actual investment outcomes.</div>', unsafe_allow_html=True,
    )


def render_asset_selection(R):
    st.title("🗂️ Asset Selection Summary")
    st.caption("Adjust your selection anytime from the sidebar's **Back to Selection** button.")

    sel_df = pd.DataFrame({
        "Symbol": R["picked_symbols"],
        "Company": [symbol_to_name.get(s, "N/A") for s in R["picked_symbols"]],
        "Sector": [symbol_to_sector.get(s, "N/A") for s in R["picked_symbols"]],
    })
    st.dataframe(sel_df, use_container_width=True)

    st.markdown('<div class="section-header">Full PSX Stock Database</div>', unsafe_allow_html=True)
    st.dataframe(stock_db, use_container_width=True, height=450)


def render_dashboard(R, active, active_label):
    st.title("📊 Portfolio Dashboard")
    st.caption(f"Mode: **{R['strategy_mode']}** | Period: {R['start_date']} to {R['end_date']}")


    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total Investment", fmt_pkr(R["investment_amount"]))
    with c2: kpi_card("Expected Annual Return", fmt_pct(active["expected_return"]))
    with c3: kpi_card("Annual Volatility", fmt_pct(active["volatility"]))
    with c4: kpi_card("Sharpe Ratio", fmt_num(active["sharpe_ratio"]))

    c5, c6, c7, c8 = st.columns(4)
    with c5: kpi_card("Portfolio Beta", fmt_num(active["beta"]), "vs. synthetic proxy")
    with c6: kpi_card("Max Drawdown", fmt_pct(active["max_drawdown"]))
    with c7: kpi_card("Est. 1-Year Value", fmt_pkr(active["fv_1y"]))
    with c8: kpi_card("Est. 5-Year Value", fmt_pkr(active["fv_5y"]))

    
# PORTOLIO ALLOCATION

    st.markdown('<div class="section-header">Portfolio Allocation</div>', unsafe_allow_html=True)
    hide_zero = st.checkbox("Hide zero-weight assets in chart", value=True, key="hide_zero")
    col_table, col_chart = st.columns([1.4, 1])
    with col_table:
        alloc_table = active["weights"].reset_index()
        alloc_table.columns = ["Symbol", "Weight"]
        alloc_table["Company"] = alloc_table["Symbol"].map(symbol_to_name)
        alloc_table["Sector"] = alloc_table["Symbol"].map(symbol_to_sector)
        alloc_table["Investment (PKR)"] = alloc_table["Weight"] * R["investment_amount"]
        alloc_table["Weight"] = (alloc_table["Weight"] * 100).round(2).astype(str) + "%"
        alloc_table["Investment (PKR)"] = alloc_table["Investment (PKR)"].apply(lambda x: f"Rs. {x:,.0f}")
        st.dataframe(alloc_table[["Company", "Symbol", "Sector", "Weight", "Investment (PKR)"]], use_container_width=True, height=420)
    st.caption("A zero weight does not mean a company is permanently a bad investment — it only means the optimizer did not require it under the selected historical period, assets, and constraints.")
    with col_chart:
        fig = viz.allocation_donut_chart(active["weights"], symbol_to_name, R["investment_amount"], active_label, hide_zero)
        st.plotly_chart(fig, use_container_width=True)

# STRATEGY COMPARISON
        
    if R["strategy_mode"] == "Compare Both":
        st.markdown('<div class="section-header">Strategy Comparison</div>', unsafe_allow_html=True)
        comp = pd.DataFrame({
            "Metric": ["Expected Annual Return", "Annual Volatility", "Sharpe Ratio", "Beta", "Max Drawdown", "Est. 1Y Value", "Est. 5Y Value"],
            "Maximum Sharpe Ratio": [
                fmt_pct(R["packages"]["Maximum Sharpe Ratio"]["expected_return"]),
                fmt_pct(R["packages"]["Maximum Sharpe Ratio"]["volatility"]),
                fmt_num(R["packages"]["Maximum Sharpe Ratio"]["sharpe_ratio"]),
                fmt_num(R["packages"]["Maximum Sharpe Ratio"]["beta"]),
                fmt_pct(R["packages"]["Maximum Sharpe Ratio"]["max_drawdown"]),
                fmt_pkr(R["packages"]["Maximum Sharpe Ratio"]["fv_1y"]),
                fmt_pkr(R["packages"]["Maximum Sharpe Ratio"]["fv_5y"]),
            ],
            "Minimum Volatility": [
                fmt_pct(R["packages"]["Minimum Volatility"]["expected_return"]),
                fmt_pct(R["packages"]["Minimum Volatility"]["volatility"]),
                fmt_num(R["packages"]["Minimum Volatility"]["sharpe_ratio"]),
                fmt_num(R["packages"]["Minimum Volatility"]["beta"]),
                fmt_pct(R["packages"]["Minimum Volatility"]["max_drawdown"]),
                fmt_pkr(R["packages"]["Minimum Volatility"]["fv_1y"]),
                fmt_pkr(R["packages"]["Minimum Volatility"]["fv_5y"]),
            ],
        })
        st.dataframe(comp, use_container_width=True, hide_index=True)
        st.caption(f"Detailed sections below use the **{active_label}** portfolio — switch via 'Viewing strategy' in the sidebar.")

    st.markdown('<div class="section-header">Individual Stocks vs. Optimized Portfolio</div>', unsafe_allow_html=True)
    display_table = R["stock_table"].copy()
    port_daily = R["returns_df"] @ active["weights"].reindex(R["returns_df"].columns).fillna(0).values
    port_row = pd.DataFrame([{
        "Avg Daily Return": port_daily.mean(), "Daily Volatility": port_daily.std(),
        "Expected Annual Return": active["expected_return"], "Annual Volatility": active["volatility"],
        "Sharpe Ratio": active["sharpe_ratio"], "Beta": active["beta"], "Max Drawdown": active["max_drawdown"],
        "1-Year Hypothetical Value": active["fv_1y"], "5-Year Hypothetical Value": active["fv_5y"],
    }], index=[f"Optimized Portfolio ({active_label})"])
    display_table = pd.concat([display_table, port_row])
    fmt_table = display_table.copy()
    for col in ["Avg Daily Return", "Daily Volatility", "Expected Annual Return", "Annual Volatility", "Max Drawdown"]:
        fmt_table[col] = fmt_table[col].apply(fmt_pct)
    fmt_table["Sharpe Ratio"] = fmt_table["Sharpe Ratio"].apply(fmt_num)
    fmt_table["Beta"] = fmt_table["Beta"].apply(fmt_num)
    fmt_table["1-Year Hypothetical Value"] = fmt_table["1-Year Hypothetical Value"].apply(fmt_pkr)
    fmt_table["5-Year Hypothetical Value"] = fmt_table["5-Year Hypothetical Value"].apply(fmt_pkr)
    st.dataframe(fmt_table, use_container_width=True)
    st.caption("Future values are hypothetical estimates based on historical annualized returns — not guaranteed predictions.")

    st.markdown('<div class="section-header">Risk vs. Return Analysis</div>', unsafe_allow_html=True)
    fig2 = viz.risk_return_scatter(R["stock_table"], R["packages"]["Maximum Sharpe Ratio"], R["packages"]["Minimum Volatility"], active, active_label)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Efficient Frontier</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">The Efficient Frontier represents portfolios that provide the highest estimated '
        'expected return for a given level of estimated risk, under the model assumptions.</div>', unsafe_allow_html=True)
    fig3 = viz.efficient_frontier_chart(R["sim_df"], R["frontier_df"], R["packages"]["Maximum Sharpe Ratio"], R["packages"]["Minimum Volatility"])
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-header">Maximum Drawdown</div>', unsafe_allow_html=True)
    st.write("Maximum Drawdown represents the largest historical peak-to-trough decline during the analyzed period.")
    fig4 = viz.drawdown_chart(active["drawdown_series"], f"{active_label} Portfolio Drawdown")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-header">Automated Summary</div>', unsafe_allow_html=True)
    tbl = R["stock_table"]
    best_return_stock = tbl["Expected Annual Return"].idxmax()
    lowest_vol_stock = tbl["Annual Volatility"].idxmin()
    best_sharpe_stock = tbl["Sharpe Ratio"].idxmax()
    lowest_dd_stock = tbl["Max Drawdown"].idxmax()

    st.markdown(f"""
    Under the selected historical period ({R['start_date']} to {R['end_date']}) and model assumptions:

    - **{best_return_stock}** had the highest historical annualized return among selected stocks ({fmt_pct(tbl.loc[best_return_stock, 'Expected Annual Return'])}).
    - **{lowest_vol_stock}** had the lowest annualized volatility ({fmt_pct(tbl.loc[lowest_vol_stock, 'Annual Volatility'])}).
    - **{best_sharpe_stock}** had the highest historical Sharpe Ratio ({fmt_num(tbl.loc[best_sharpe_stock, 'Sharpe Ratio'])}).
    - **{lowest_dd_stock}** had the smallest maximum drawdown ({fmt_pct(tbl.loc[lowest_dd_stock, 'Max Drawdown'])}).
    - The **{active_label}** portfolio produced an estimated annual return of {fmt_pct(active['expected_return'])}, volatility of {fmt_pct(active['volatility'])}, and Sharpe Ratio of {fmt_num(active['sharpe_ratio'])}.
    - Estimated 1-year hypothetical value: {fmt_pkr(active['fv_1y'])}. Estimated 5-year hypothetical value: {fmt_pkr(active['fv_5y'])}.
    - Compared with placing the entire amount in the highest-volatility individual stock, the optimized portfolio's estimated volatility was {"lower" if active["volatility"] < tbl["Annual Volatility"].max() else "not lower"}, reflecting the effect of diversification under the observed correlations.

    This is not a recommendation to buy or sell any specific security.
    """)

    st.markdown(
        '<div class="disclaimer-box">This application is intended for educational and analytical purposes only and does not '
        'constitute financial, investment, legal, or tax advice. Historical performance does not guarantee future results.</div>',
        unsafe_allow_html=True,
    )


def render_backtesting(R):
    st.title("🔁 Historical Backtesting")
    st.caption("Weights are calculated using the training period ONLY, then applied unchanged to the out-of-sample test period.")

    series_dict = {label: res["cumulative_value"] for label, res in R["backtest_results"].items()}
    fig = viz.backtest_growth_chart(series_dict, R["investment_amount"])
    st.plotly_chart(fig, use_container_width=True)

    bt_rows = []
    for label, res in R["backtest_results"].items():
        bt_rows.append({
            "Strategy": label, "Total Test Return": fmt_pct(res["total_return"]),
            "Annualized Return": fmt_pct(res["annualized_return"]), "Annualized Volatility": fmt_pct(res["annualized_volatility"]),
            "Sharpe Ratio": fmt_num(res["sharpe_ratio"]), "Max Drawdown": fmt_pct(res["max_drawdown"]),
            "Final Value": fmt_pkr(res["final_value"]),
        })
    st.dataframe(pd.DataFrame(bt_rows), use_container_width=True, hide_index=True)
    st.caption("This is a Historical Backtest, not a future prediction.")


def render_analytics(R):
    st.title("🔬 Analytics")

    st.markdown('<div class="section-header">Correlation Heatmap</div>', unsafe_allow_html=True)
    st.plotly_chart(viz.correlation_heatmap(R["corr_matrix"]), use_container_width=True)
    st.caption(
        "Correlation near +1: assets historically moved in similar directions. Near 0: weak historical linear "
        "relationship. Near -1: assets historically moved in opposite directions."
    )

    with st.expander("Annualized Covariance Matrix"):
        st.dataframe(R["cov_matrix"].round(6), use_container_width=True)

    st.markdown('<div class="section-header">Beta Analysis (vs. Synthetic Proxy Benchmark)</div>', unsafe_allow_html=True)
    st.caption("Proxy = equal-weighted average of all stocks in the local dataset (not the official KSE-100).")
    if R["benchmark_returns"].empty:
        st.warning("Benchmark proxy unavailable for this date range — Beta values cannot be shown.")
    else:
        beta_rows = []
        for symbol in R["returns_df"].columns:
            b = R["stock_table"].loc[symbol, "Beta"]
            beta_rows.append({"Symbol": symbol, "Beta": fmt_num(b), "Interpretation": an.interpret_beta(b)})
        st.dataframe(pd.DataFrame(beta_rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">Top-Performing Assets</div>', unsafe_allow_html=True)
    sort_by = st.selectbox("Sort by", ["Expected Annual Return", "Sharpe Ratio", "Annual Volatility", "Max Drawdown"], key="sort_by")
    ascending = sort_by in ["Annual Volatility"]
    ranked = R["stock_table"].sort_values(sort_by, ascending=ascending)
    st.dataframe(
    ranked.style.format({
        "Avg Daily Return": "{:.2%}",
        "Daily Volatility": "{:.2%}",
        "Expected Annual Return": "{:.2%}",
        "Annual Volatility": "{:.2%}",
        "Sharpe Ratio": "{:.4f}",
        "Beta": "{:.4f}"
    }),
    use_container_width=True
)
    st.caption("Rankings are based on the selected historical period only and are not a permanent ranking.")

    st.markdown('<div class="section-header">Data Quality & Validation</div>', unsafe_allow_html=True)
    dq_rows = []
    for symbol, report in R["quality_report"].items():
        dq_rows.append({
            "Symbol": symbol, "Company": symbol_to_name.get(symbol, "N/A"), "Sector": symbol_to_sector.get(symbol, "N/A"),
            "Observations": report.get("n_observations"), "Missing Values": report.get("missing_values"),
            "First Date": report.get("first_date"), "Last Date": report.get("last_date"),
            "Warnings": "; ".join(report.get("warnings", [])) or "None",
        })
    st.dataframe(pd.DataFrame(dq_rows), use_container_width=True, hide_index=True)


def render_reports(R, active, active_label):
    st.title("📄 Export Reports")

    alloc_csv = active["weights"].reset_index()
    alloc_csv.columns = ["Symbol", "Weight"]
    alloc_csv["Investment (PKR)"] = alloc_csv["Weight"] * R["investment_amount"]
    st.download_button("⬇ Download Portfolio Allocation (CSV)", alloc_csv.to_csv(index=False), "portfolio_allocation.csv", "text/csv")

    st.download_button("⬇ Download Individual Stock Comparison (CSV)", R["stock_table"].to_csv(), "stock_comparison.csv", "text/csv")

    summary_csv = pd.DataFrame([{
        "Strategy": active_label, "Investment": R["investment_amount"],
        "Expected Annual Return": active["expected_return"], "Annual Volatility": active["volatility"],
        "Sharpe Ratio": active["sharpe_ratio"], "Portfolio Beta": active["beta"],
        "Max Drawdown": active["max_drawdown"], "1Y Value": active["fv_1y"], "5Y Value": active["fv_5y"],
    }])
    st.download_button("⬇ Download Portfolio Summary (CSV)", summary_csv.to_csv(index=False), "portfolio_summary.csv", "text/csv")


# ==================================================================
# ROUTER
# ==================================================================

if st.session_state.view == "setup" or st.session_state.results is None:
    render_setup_page()
else:
    render_results_page()
