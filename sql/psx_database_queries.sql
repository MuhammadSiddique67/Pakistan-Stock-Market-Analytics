-- ============================================================
-- PSX PORTFOLIO DATABASE - COMPLETE SQL QUERY COLLECTION
-- Database: psx_portfolio_db
-- Table: stock_prices
-- Columns: Date, Symbol, Open, High, Low, Close, Adj Close, Volume
-- ============================================================

USE psx_portfolio_db;

-- ============================================================
-- 1. DATABASE AND TABLE INSPECTION
-- ============================================================

SHOW DATABASES;
SHOW TABLES;
DESCRIBE stock_prices;

-- View sample records
SELECT *
FROM stock_prices
LIMIT 10;

-- ============================================================
-- 2. BASIC DATA VALIDATION
-- ============================================================

-- Total number of records
SELECT COUNT(*) AS total_rows
FROM stock_prices;

-- Total number of companies
SELECT COUNT(DISTINCT Symbol) AS total_companies
FROM stock_prices;

-- List all available company symbols
SELECT DISTINCT Symbol
FROM stock_prices
ORDER BY Symbol;

-- Overall date range
SELECT
    MIN(Date) AS start_date,
    MAX(Date) AS end_date
FROM stock_prices;

-- Record count and date range for every company
SELECT
    Symbol,
    COUNT(*) AS total_records,
    MIN(Date) AS start_date,
    MAX(Date) AS end_date
FROM stock_prices
GROUP BY Symbol
ORDER BY Symbol;

-- ============================================================
-- 3. MISSING-VALUE CHECKS
-- ============================================================

-- Missing values in every column
SELECT
    SUM(CASE WHEN Date IS NULL THEN 1 ELSE 0 END) AS missing_date,
    SUM(CASE WHEN Symbol IS NULL OR TRIM(Symbol) = '' THEN 1 ELSE 0 END) AS missing_symbol,
    SUM(CASE WHEN Open IS NULL THEN 1 ELSE 0 END) AS missing_open,
    SUM(CASE WHEN High IS NULL THEN 1 ELSE 0 END) AS missing_high,
    SUM(CASE WHEN Low IS NULL THEN 1 ELSE 0 END) AS missing_low,
    SUM(CASE WHEN Close IS NULL THEN 1 ELSE 0 END) AS missing_close,
    SUM(CASE WHEN `Adj Close` IS NULL THEN 1 ELSE 0 END) AS missing_adj_close,
    SUM(CASE WHEN Volume IS NULL THEN 1 ELSE 0 END) AS missing_volume
FROM stock_prices;

-- Display rows containing any missing value
SELECT *
FROM stock_prices
WHERE Date IS NULL
   OR Symbol IS NULL
   OR TRIM(Symbol) = ''
   OR Open IS NULL
   OR High IS NULL
   OR Low IS NULL
   OR Close IS NULL
   OR `Adj Close` IS NULL
   OR Volume IS NULL;

-- Missing Close prices by company
SELECT
    Symbol,
    COUNT(*) AS missing_close_values
FROM stock_prices
WHERE Close IS NULL
GROUP BY Symbol
ORDER BY missing_close_values DESC;

-- ============================================================
-- 4. DUPLICATE CHECKS
-- ============================================================

-- Duplicate Symbol-Date combinations
SELECT
    Symbol,
    Date,
    COUNT(*) AS duplicate_count
FROM stock_prices
GROUP BY Symbol, Date
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, Symbol, Date;

-- Total number of duplicate Symbol-Date groups
SELECT COUNT(*) AS duplicate_groups
FROM (
    SELECT Symbol, Date
    FROM stock_prices
    GROUP BY Symbol, Date
    HAVING COUNT(*) > 1
) AS duplicates;

-- ============================================================
-- 5. DATA-QUALITY CHECKS
-- ============================================================

-- Invalid or non-positive prices
SELECT *
FROM stock_prices
WHERE Open <= 0
   OR High <= 0
   OR Low <= 0
   OR Close <= 0
   OR `Adj Close` <= 0;

-- Invalid OHLC relationships
SELECT *
FROM stock_prices
WHERE High < Low
   OR High < Open
   OR High < Close
   OR Low > Open
   OR Low > Close;

-- Negative trading volume
SELECT *
FROM stock_prices
WHERE Volume < 0;

-- Companies with the fewest observations
SELECT
    Symbol,
    COUNT(*) AS total_records
FROM stock_prices
GROUP BY Symbol
ORDER BY total_records ASC, Symbol
LIMIT 20;

-- ============================================================
-- 6. COMPANY-SPECIFIC QUERIES
-- ============================================================

-- Latest 10 MEBL records
SELECT *
FROM stock_prices
WHERE Symbol = 'MEBL'
ORDER BY Date DESC
LIMIT 10;

-- Complete MEBL price history
SELECT *
FROM stock_prices
WHERE Symbol = 'MEBL'
ORDER BY Date;

-- Selected companies for portfolio analysis
SELECT *
FROM stock_prices
WHERE Symbol IN ('MEBL', 'HBL', 'LUCK', 'OGDC', 'PSO')
ORDER BY Date, Symbol;

-- Selected companies within a date range
SELECT *
FROM stock_prices
WHERE Symbol IN ('MEBL', 'HBL', 'LUCK', 'OGDC', 'PSO')
  AND Date BETWEEN '2020-01-01' AND '2025-12-31'
ORDER BY Date, Symbol;

-- ============================================================
-- 7. LATEST MARKET DATA
-- ============================================================

-- Latest available date in the database
SELECT MAX(Date) AS latest_market_date
FROM stock_prices;

-- All company records on the latest available date
SELECT sp.*
FROM stock_prices AS sp
WHERE sp.Date = (
    SELECT MAX(Date)
    FROM stock_prices
)
ORDER BY sp.Symbol;

-- Latest available record for every company
SELECT sp.*
FROM stock_prices AS sp
INNER JOIN (
    SELECT
        Symbol,
        MAX(Date) AS latest_date
    FROM stock_prices
    GROUP BY Symbol
) AS latest
    ON sp.Symbol = latest.Symbol
   AND sp.Date = latest.latest_date
ORDER BY sp.Symbol;

-- ============================================================
-- 8. PRICE AND VOLUME SUMMARY
-- ============================================================

-- Price summary for every company
SELECT
    Symbol,
    COUNT(*) AS observations,
    ROUND(AVG(Close), 2) AS average_close,
    ROUND(MIN(Close), 2) AS minimum_close,
    ROUND(MAX(Close), 2) AS maximum_close,
    ROUND(AVG(Volume), 0) AS average_volume,
    MAX(Volume) AS maximum_volume
FROM stock_prices
GROUP BY Symbol
ORDER BY Symbol;

-- Top 10 companies by average trading volume
SELECT
    Symbol,
    ROUND(AVG(Volume), 0) AS average_volume
FROM stock_prices
GROUP BY Symbol
ORDER BY average_volume DESC
LIMIT 10;

-- Top 10 highest closing-price records
SELECT
    Date,
    Symbol,
    Close
FROM stock_prices
WHERE Close IS NOT NULL
ORDER BY Close DESC
LIMIT 10;

-- ============================================================
-- 9. YEARLY ANALYSIS
-- ============================================================

-- Yearly price and volume summary by company
SELECT
    Symbol,
    YEAR(Date) AS trading_year,
    ROUND(AVG(Close), 2) AS average_close,
    ROUND(MIN(Close), 2) AS minimum_close,
    ROUND(MAX(Close), 2) AS maximum_close,
    SUM(Volume) AS total_volume
FROM stock_prices
GROUP BY Symbol, YEAR(Date)
ORDER BY Symbol, trading_year;

-- Yearly MEBL summary
SELECT
    YEAR(Date) AS trading_year,
    ROUND(AVG(Close), 2) AS average_close,
    ROUND(MIN(Close), 2) AS minimum_close,
    ROUND(MAX(Close), 2) AS maximum_close,
    SUM(Volume) AS total_volume
FROM stock_prices
WHERE Symbol = 'MEBL'
GROUP BY YEAR(Date)
ORDER BY trading_year;

-- ============================================================
-- 10. DAILY RETURN ANALYSIS (MYSQL 8.0+)
-- ============================================================

-- Daily returns for MEBL using adjusted closing prices
WITH price_history AS (
    SELECT
        Date,
        Symbol,
        `Adj Close`,
        LAG(`Adj Close`) OVER (
            PARTITION BY Symbol
            ORDER BY Date
        ) AS previous_adj_close
    FROM stock_prices
    WHERE Symbol = 'MEBL'
)
SELECT
    Date,
    Symbol,
    `Adj Close`,
    previous_adj_close,
    ROUND(
        (`Adj Close` / previous_adj_close - 1) * 100,
        4
    ) AS daily_return_percent
FROM price_history
WHERE previous_adj_close IS NOT NULL
ORDER BY Date;

-- Average daily return and daily volatility for every company
WITH daily_returns AS (
    SELECT
        Date,
        Symbol,
        (`Adj Close` / LAG(`Adj Close`) OVER (
            PARTITION BY Symbol
            ORDER BY Date
        )) - 1 AS daily_return
    FROM stock_prices
    WHERE `Adj Close` IS NOT NULL
)
SELECT
    Symbol,
    COUNT(daily_return) AS return_observations,
    ROUND(AVG(daily_return) * 100, 4) AS average_daily_return_percent,
    ROUND(STDDEV_SAMP(daily_return) * 100, 4) AS daily_volatility_percent
FROM daily_returns
WHERE daily_return IS NOT NULL
GROUP BY Symbol
ORDER BY daily_volatility_percent DESC;

-- ============================================================
-- 11. OPTIONAL PERFORMANCE INDEXES
-- Run once after confirming the table is clean.
-- ============================================================

-- Index for faster company/date filtering
-- CREATE INDEX idx_stock_symbol_date
-- ON stock_prices (Symbol(20), Date);

-- Index for faster date filtering
-- CREATE INDEX idx_stock_date
-- ON stock_prices (Date);

-- ============================================================
-- END OF SCRIPT
-- Portfolio optimization, covariance matrices, Sharpe ratio,
-- beta, efficient frontier and charts should remain in Python.
-- ============================================================
