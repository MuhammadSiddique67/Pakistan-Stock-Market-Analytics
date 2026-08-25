"""
visualization.py

All Plotly chart builders for the PSX Portfolio Optimizer dashboard.
Every chart is built from real calculated data passed in by app.py —
no hard-coded figures.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Theme colors
BG_COLOR = "#0f1229"
CARD_COLOR = "#171b3a"
PURPLE = "#8b5cf6"
VIOLET = "#a78bfa"
TEXT_COLOR = "#e5e7f5"
GRID_COLOR = "#2a2f52"
GREEN = "#34d399"
RED = "#f87171"

CHART_LAYOUT = dict(
    paper_bgcolor=BG_COLOR,
    plot_bgcolor=BG_COLOR,
    font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def allocation_donut_chart(weights: pd.Series, symbol_to_name: dict, investment: float, center_label: str, hide_zero: bool = False):
    df = weights.reset_index()
    df.columns = ["Symbol", "Weight"]
    df["Company"] = df["Symbol"].map(symbol_to_name).fillna(df["Symbol"])
    df["Investment"] = df["Weight"] * investment

    if hide_zero:
        df = df[df["Weight"] > 0.0001]

    fig = go.Figure(data=[go.Pie(
        labels=df["Symbol"],
        values=df["Weight"],
        hole=0.62,
        marker=dict(colors=px.colors.sequential.Purples_r[:len(df)] or [PURPLE] * len(df), line=dict(color=BG_COLOR, width=2)),
        customdata=np.stack([df["Company"], df["Investment"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>Symbol: %{label}<br>Weight: %{percent}<br>Investment: PKR %{customdata[1]:,.0f}<extra></extra>",
        textinfo="label+percent",
        textfont=dict(color=TEXT_COLOR, size=12),
    )])

    fig.update_layout(
        **CHART_LAYOUT,
        annotations=[dict(text=f"{center_label}<br><b>Rs. {investment:,.0f}</b>", x=0.5, y=0.5, font_size=14, showarrow=False, font_color=TEXT_COLOR)],
        showlegend=True,
        height=450,
    )
    return fig


def risk_return_scatter(stock_stats: pd.DataFrame, max_sharpe_pt: dict, min_vol_pt: dict, selected_strategy_pt: dict, strategy_name: str):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_stats["Annual Volatility"] * 100,
        y=stock_stats["Expected Annual Return"] * 100,
        mode="markers+text",
        text=stock_stats.index,
        textposition="top center",
        marker=dict(size=12, color=VIOLET, line=dict(width=1, color=TEXT_COLOR)),
        name="Individual Stocks",
        hovertemplate="<b>%{text}</b><br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[max_sharpe_pt["volatility"] * 100], y=[max_sharpe_pt["expected_return"] * 100],
        mode="markers", marker=dict(size=18, color=GREEN, symbol="star"),
        name="Max Sharpe Portfolio",
        hovertemplate="Max Sharpe<br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[min_vol_pt["volatility"] * 100], y=[min_vol_pt["expected_return"] * 100],
        mode="markers", marker=dict(size=18, color="#fbbf24", symbol="diamond"),
        name="Min Volatility Portfolio",
        hovertemplate="Min Volatility<br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[selected_strategy_pt["volatility"] * 100], y=[selected_strategy_pt["expected_return"] * 100],
        mode="markers", marker=dict(size=20, color=PURPLE, symbol="x", line=dict(width=2, color="white")),
        name=f"Selected: {strategy_name}",
        hovertemplate="Selected Strategy<br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        xaxis=dict(title="Annual Volatility (%)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Expected Annual Return (%)", gridcolor=GRID_COLOR),
        height=500,
        title="Risk vs. Return: Individual Stocks vs. Optimized Portfolios",
    )
    return fig


def efficient_frontier_chart(sim_df: pd.DataFrame, frontier_df: pd.DataFrame, max_sharpe_pt: dict, min_vol_pt: dict):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=sim_df["volatility"] * 100, y=sim_df["expected_return"] * 100,
        mode="markers",
        marker=dict(
            size=5, color=sim_df["sharpe_ratio"], colorscale="Purples",
            colorbar=dict(title="Sharpe"), opacity=0.6,
        ),
        name="Simulated Portfolios",
        hovertemplate="Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>",
    ))

    if not frontier_df.empty:
        fig.add_trace(go.Scatter(
            x=frontier_df["volatility"] * 100, y=frontier_df["target_return"] * 100,
            mode="lines", line=dict(color=TEXT_COLOR, width=3),
            name="Efficient Frontier",
        ))

    fig.add_trace(go.Scatter(
        x=[max_sharpe_pt["volatility"] * 100], y=[max_sharpe_pt["expected_return"] * 100],
        mode="markers", marker=dict(size=18, color=GREEN, symbol="star"),
        name="Max Sharpe Portfolio",
    ))

    fig.add_trace(go.Scatter(
        x=[min_vol_pt["volatility"] * 100], y=[min_vol_pt["expected_return"] * 100],
        mode="markers", marker=dict(size=18, color="#fbbf24", symbol="diamond"),
        name="Min Volatility Portfolio",
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        xaxis=dict(title="Annual Volatility (%)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Expected Annual Return (%)", gridcolor=GRID_COLOR),
        height=550,
        title="Efficient Frontier",
    )
    return fig


def correlation_heatmap(corr_matrix: pd.DataFrame):
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale="RdPu",
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        colorbar=dict(title="Correlation"),
    ))
    fig.update_layout(**CHART_LAYOUT, height=500, title="Correlation Heatmap")
    return fig


def drawdown_chart(drawdown_series: pd.Series, title: str = "Drawdown Over Time"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown_series.index, y=drawdown_series.values * 100,
        fill="tozeroy", line=dict(color=RED),
        name="Drawdown",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        xaxis=dict(title="Date", gridcolor=GRID_COLOR),
        yaxis=dict(title="Drawdown (%)", gridcolor=GRID_COLOR),
        height=350,
        title=title,
    )
    return fig


def backtest_growth_chart(series_dict: dict, investment: float):
    """series_dict: {label: pd.Series of cumulative portfolio value}"""
    fig = go.Figure()
    colors = [PURPLE, GREEN, "#fbbf24", VIOLET, "#60a5fa", RED]
    for i, (label, series) in enumerate(series_dict.items()):
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            mode="lines", name=label,
            line=dict(color=colors[i % len(colors)], width=2.5),
        ))
    fig.add_hline(y=investment, line_dash="dot", line_color=TEXT_COLOR, opacity=0.4, annotation_text="Initial Investment")
    fig.update_layout(
        **CHART_LAYOUT,
        xaxis=dict(title="Date", gridcolor=GRID_COLOR),
        yaxis=dict(title="Portfolio Value (PKR)", gridcolor=GRID_COLOR),
        height=500,
        title="Historical Backtest: Portfolio Growth (Out-of-Sample)",
    )
    return fig
