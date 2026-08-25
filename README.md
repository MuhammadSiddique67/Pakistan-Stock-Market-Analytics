#  Pakistan Stock Market Analytics & Portfolio Optimization

An end-to-end **data analytics, financial modeling, and portfolio optimization project** developed for the **Pakistan Stock Exchange (PSX)**.

The project analyzes historical stock market data and provides investors with an interactive platform to evaluate stocks, understand risk and return, and construct diversified portfolios using **Modern Portfolio Theory (Mean-Variance Optimization)**.

The project combines **Python, financial analytics, data engineering, optimization techniques, and Streamlit dashboard development** into a single investment analysis platform.

---

##  Project Overview

Investors often need to compare multiple assets based on their expected returns, volatility, correlation, and risk-adjusted performance before constructing a portfolio.

This project addresses that problem by providing a complete workflow:

**Data Collection → Data Cleaning → Financial Analysis → Risk Analysis → Portfolio Optimization → Backtesting → Interactive Dashboard**

Users can select assets, define their investment amount and risk-free rate, choose an optimization strategy, and analyze the resulting portfolio allocation and performance.

---

##  Project Objectives

The main objectives of this project are:

* Analyze historical stock market data from the Pakistani market.
* Clean and standardize financial datasets from multiple sources.
* Handle missing values, abnormal observations, and stock splits.
* Calculate historical returns and risk metrics.
* Analyze relationships between different assets.
* Construct diversified investment portfolios.
* Apply Modern Portfolio Theory to optimize portfolio allocations.
* Compare Maximum Sharpe Ratio and Minimum Risk strategies.
* Visualize portfolio performance through an interactive dashboard.
* Perform portfolio backtesting using historical data.
* Provide investors with practical portfolio decision-support tools.
* Develop a foundation for future real-time market data integration.

---

#  Key Features

## 1. Historical Market Data

The project works with historical data for **100+ companies listed on the Pakistan Stock Exchange**.

The dataset contains more than **10 years of historical market information** where available.

Data sources include:

* Yahoo Finance
* Investing.com
* Pakistan Stock Exchange (PSX)

Historical data is processed and standardized before being used for financial analysis and optimization.

---

## 2. Data Collection & Processing

The data pipeline handles:

* Historical price collection
* Multiple company datasets
* Date standardization
* Column standardization
* Missing dates
* Missing values
* Duplicate observations
* Inconsistent datasets
* Stock split adjustments
* Data validation

The objective is to create a reliable dataset that can be used for return and risk calculations.

---

## 3. Data Cleaning & Quality Control

Financial datasets can contain abnormal price movements caused by events such as stock splits, missing observations, or inconsistent price adjustments.

The project therefore includes processes for:

* Detecting missing values
* Detecting duplicate records
* Identifying abnormal price movements
* Detecting potential stock splits
* Adjusting historical price data when required
* Validating return calculations
* Standardizing datasets across companies

This helps reduce distortions in portfolio optimization results.

---

#  Financial Analysis

The project calculates several financial indicators for individual assets.

### Return Metrics

* Daily Return
* Average Daily Return
* Annualized Return
* Cumulative Return

### Risk Metrics

* Daily Volatility
* Annualized Volatility
* Portfolio Volatility
* Maximum Drawdown

### Relationship Metrics

* Correlation Matrix
* Covariance Matrix
* Portfolio Beta

### Risk-Adjusted Performance

* Sharpe Ratio

These metrics help compare assets before portfolio construction.

---

#  Correlation Analysis

The project calculates correlations between selected assets to understand how their prices and returns move relative to each other.

A correlation matrix and heatmap can be used to identify:

* Highly correlated assets
* Low-correlation assets
* Potential diversification opportunities
* Relationships between different sectors

Lower correlations can help construct more diversified portfolios.

---

#  Portfolio Optimization

The project uses **Modern Portfolio Theory (MPT)** and **Mean-Variance Optimization** to construct portfolios.

The optimization framework considers:

* Expected returns
* Asset volatility
* Covariance between assets
* Portfolio risk
* Risk-free rate
* Portfolio weights

The system generates optimized allocations based on different investment objectives.

---

#  Maximum Sharpe Ratio Portfolio

The Maximum Sharpe Ratio strategy attempts to find the portfolio with the highest **risk-adjusted return**.

The Sharpe Ratio is calculated as:

**Sharpe Ratio = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility**

This strategy is designed for investors who want to maximize return relative to the level of risk taken.

---

#  Minimum Risk Portfolio

The Minimum Risk strategy attempts to construct the portfolio with the lowest possible volatility under the defined portfolio constraints.

This approach is suitable for investors who prioritize:

* Lower volatility
* Risk reduction
* Diversification
* Capital preservation

---

#  Efficient Frontier

The project generates an **Efficient Frontier** to visualize the relationship between portfolio risk and expected return.

The Efficient Frontier helps identify portfolios that provide the best expected return for a given level of risk.

The dashboard can display:

* Portfolio risk
* Expected return
* Minimum-risk portfolio
* Maximum-Sharpe portfolio
* Individual assets
* Efficient portfolio combinations

---

# Portfolio Allocation

Users can select multiple assets and generate optimized portfolio weights.

For example:

| Asset   | Allocation |
| ------- | ---------: |
| Stock A |        25% |
| Stock B |        20% |
| Stock C |        30% |
| Stock D |        15% |
| Stock E |        10% |

The actual allocation depends on the selected assets, historical data, risk-free rate, and optimization strategy.

---

#  Interactive Streamlit Dashboard

The project includes an interactive dashboard developed using **Streamlit**.

Users can configure their portfolio through the dashboard.

### User Inputs

* Investment Amount
* Risk-Free Rate
* Sector Selection
* Stock Selection
* Selected Assets
* Optimization Strategy

### Portfolio Strategies

* Maximum Sharpe Ratio
* Minimum Risk

---

#  Dashboard Components

The portfolio dashboard provides several important metrics and visualizations.

### KPI Cards

* Total Investment
* Expected Annual Return
* Annual Volatility
* Sharpe Ratio
* Portfolio Beta
* Maximum Drawdown

### Visualizations

* Portfolio Allocation
* Efficient Frontier
* Risk vs Return
* Correlation Heatmap
* Portfolio Comparison
* Backtesting Results
* Performance Analysis

---

# 📈 Portfolio Backtesting

The project includes historical backtesting to evaluate how an optimized portfolio would have performed using historical market data.

Backtesting helps analyze:

* Initial investment
* Portfolio growth
* Historical portfolio value
* Returns
* Drawdowns
* Risk characteristics
* Strategy performance

This allows users to evaluate the historical behavior of different portfolio strategies.

> **Note:** Historical backtesting results do not guarantee future investment performance.

---

# 🔮 Five-Year Portfolio Projection

The dashboard provides an estimated future portfolio value based on the calculated expected return.

Users can enter an initial investment amount and view an estimated portfolio value after **5 years**.

This feature is intended for analytical and educational purposes rather than guaranteed investment forecasting.

---

# 🛠️ Technology Stack

## Programming

* Python

## Data Analysis

* Pandas
* NumPy

## Financial & Mathematical Analysis

* SciPy

## Data Visualization

* Matplotlib
* Seaborn
* Plotly

## Dashboard

* Streamlit

## Database & Querying

* SQL

## Data Sources

* Yahoo Finance
* Investing.com
* Pakistan Stock Exchange (PSX)

## Development Tools

* Visual Studio Code
* Jupyter Notebook
* Git
* GitHub

---

# 📚 Python Libraries

The main Python libraries used in the project include:

```text
pandas
numpy
scipy
matplotlib
seaborn
plotly
streamlit
yfinance
```

Additional libraries may be used depending on the individual modules and data pipeline.

---

# 🗂️ Project Structure

```text
Pakistan-Stock-Market-Analytics/
│
├── streamlit_app/
│   │
│   ├── app.py
│   ├── analytics.py
│   ├── data_fetcher.py
│   └── render_setup_page.py
│
├── notebooks/
│   │
│   ├── 01_PSX_Data_Collection.ipynb
│   ├── SQL_Integration.ipynb
│   ├── 02_Stock_Return_and_Risk_Analysis.ipynb
│   └── 03_Portfolio_Optimization.ipynb
│
├── data/
│   │
│   └── Historical market datasets
│
├── assets/
│   │
│   └── Dashboard images and supporting files
│
├── requirements.txt
│
├── README.md
│
└── .gitignore
```

---

# 🔄 Project Workflow

```text
             Historical Market Data
                     │
                     ▼
              Data Collection
                     │
                     ▼
             Data Preprocessing
                     │
                     ▼
              Data Cleaning
                     │
                     ▼
        Returns & Risk Calculation
                     │
                     ▼
        Correlation & Covariance
                     │
                     ▼
          Portfolio Optimization
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
 Maximum Sharpe             Minimum Risk
   Portfolio                  Portfolio
          │                     │
          └──────────┬──────────┘
                     ▼
             Portfolio Analysis
                     │
                     ▼
               Backtesting
                     │
                     ▼
          Interactive Dashboard
```

---

# 📐 Portfolio Optimization Methodology

The optimization process follows the principles of Modern Portfolio Theory.

For a portfolio containing multiple assets, portfolio return is calculated using the weighted expected returns of the assets.

Portfolio risk is determined using the covariance between asset returns.

The optimization process searches for portfolio weights that satisfy the defined constraints while optimizing the selected objective.

### Portfolio Constraints

The optimization framework can include:

* Fully invested portfolio
* Portfolio weights summing to 100%
* Non-negative asset weights
* Maximum number of selected assets
* User-selected investment universe

---

# 📊 Risk Metrics

The project evaluates portfolio performance using several risk metrics.

### Volatility

Measures the variability of portfolio returns.

### Sharpe Ratio

Measures risk-adjusted performance.

### Beta

Measures portfolio sensitivity relative to the selected benchmark or market reference.

### Maximum Drawdown

Measures the largest decline from a previous portfolio peak.

These metrics provide a broader understanding of portfolio risk instead of relying only on expected return.

---

# 🧹 Data Quality Challenges

Working with historical Pakistani stock market data introduces several practical challenges.

The project addresses issues including:

* Different historical date ranges
* Missing observations
* Different company listing dates
* Stock splits
* Unadjusted prices
* Adjusted prices from different providers
* Inconsistent historical records
* Different data availability across companies

These issues are considered during the preprocessing and analysis stages to improve the reliability of the final portfolio results.

---

# 📦 Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/Pakistan-Stock-Market-Analytics.git
```

Move into the project directory:

```bash
cd Pakistan-Stock-Market-Analytics
```

Install the required Python libraries:

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Dashboard

Navigate to the Streamlit application directory if required and run:

```bash
streamlit run app.py
```

The Streamlit application will open in your browser.

---

# 💻 Example Use Case

An investor can:

1. Enter an investment amount.
2. Select a risk-free rate.
3. Select sectors.
4. Choose individual stocks.
5. Select an optimization strategy.
6. Run the optimization.
7. Review the recommended portfolio allocation.
8. Compare expected return and risk.
9. Analyze the Efficient Frontier.
10. Review portfolio KPIs.
11. Examine historical backtesting results.
12. Estimate the portfolio's future value.

---

# 🚧 Future Development

The project is currently being extended with additional automation and real-time capabilities.

### 🔴 Live Market Data Integration

A planned feature is to automatically fetch the latest available stock prices instead of relying only on manually updated historical files.

### 🔄 Automated Data Updates

The future data pipeline will:

* Fetch daily stock prices automatically.
* Update the historical database.
* Maintain a rolling 10-year dataset.
* Recalculate daily returns.
* Update volatility and risk metrics.
* Refresh portfolio optimization results.

### ⚡ Real-Time Dashboard Updates

The dashboard will eventually be connected to the automated data pipeline so that portfolio analysis can be updated whenever new market data becomes available.

### 🗄️ SQL Database Integration

The project can be further developed into a centralized financial database containing:

* Company information
* Historical prices
* Daily returns
* Risk metrics
* Sector classifications
* Portfolio data

This would make the system more scalable and suitable for automated analytics.

---

# Disclaimer

This project is developed for **educational, analytical, and portfolio research purposes**.

The portfolio allocations, expected returns, projections, and historical backtesting results generated by this system should not be considered financial advice.

Historical performance does not guarantee future results.

Investors should conduct their own research and consider their individual financial objectives and risk tolerance before making investment decisions.

---

#  Author

## Muhammad Siddique Malik

**BS Computational Finance**
NED University of Engineering & Technology, Karachi

Interested in:

* Data Analytics
* Financial Analytics
* Quantitative Finance
* Portfolio Optimization
* Python Development
* Financial Data Engineering
* Business Intelligence
* FinTech

---

#  Project Highlights

This project demonstrates practical experience in:

**Python → Data Collection → Data Cleaning → Financial Analysis → Risk Modeling → Optimization → Backtesting → Dashboard Development**

It combines financial theory with practical data analytics and software development to create a complete investment decision-support platform for the Pakistan Stock Market.

---

##  Project Status

**Current Status:** 🟢 Active Development

The core portfolio optimization and interactive dashboard are developed. Additional features including automated live data collection, rolling historical updates, SQL integration, and real-time dashboard updates are planned for future development.
