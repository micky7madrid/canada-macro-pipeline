-- Q1 (US-1): latest value of every indicator
SELECT i.indicator_name, d.full_date AS latest_date, f.value
FROM fact_indicator f
JOIN dim_date d      ON f.date_key = d.date_key
JOIN dim_indicator i ON f.indicator_code = i.indicator_code
WHERE f.date_key = (
    SELECT MAX(f2.date_key)
    FROM fact_indicator f2
    WHERE f2.indicator_code = f.indicator_code
)
ORDER BY i.indicator_name;

-- Q2 (US-2): monthly average of the daily indicators
SELECT
    d.year,
    d.month,
    i.indicator_name,
    ROUND(AVG(f.value), 3) AS avg_value
FROM fact_indicator f
JOIN dim_date d      ON f.date_key = d.date_key
JOIN dim_indicator i ON f.indicator_code = i.indicator_code
WHERE f.indicator_code IN ('V39079', 'FXUSDCAD', 'BD.CDN.10YR.DQ.YLD')
GROUP BY d.year, d.month, i.indicator_name
ORDER BY d.year, d.month, i.indicator_name;

-- Q3 (US-2): USD/CAD range and average
SELECT
    MIN(f.value)            AS lowest,
    MAX(f.value)            AS highest,
    ROUND(AVG(f.value), 4)  AS average,
    COUNT(*)                AS days_of_data
FROM fact_indicator f
WHERE f.indicator_code = 'FXUSDCAD';

-- Q3b: the 5 days USD/CAD was highest
SELECT TOP 5 d.full_date, f.value
FROM fact_indicator f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.indicator_code = 'FXUSDCAD'
ORDER BY f.value DESC;

-- Q3b: the 5 days USD/CAD was highest
SELECT TOP 5 d.full_date, f.value
FROM fact_indicator f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.indicator_code = 'FXUSDCAD'
ORDER BY f.value DESC;

-- Q4a (US-2): USD/CAD average by weekday
SELECT
    d.day_of_week,
    COUNT(*)               AS days,
    ROUND(AVG(f.value), 4) AS avg_usdcad
FROM fact_indicator f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.indicator_code = 'FXUSDCAD'
GROUP BY d.day_of_week
ORDER BY MIN(DATEPART(weekday, d.full_date));

-- Q4b (US-2): USD/CAD average by quarter
SELECT
    d.year,
    d.quarter,
    COUNT(*)               AS days,
    ROUND(AVG(f.value), 4) AS avg_usdcad
FROM fact_indicator f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.indicator_code = 'FXUSDCAD'
GROUP BY d.year, d.quarter
ORDER BY d.year, d.quarter;

-- Q5 (US-1): dates the policy rate changed
WITH rate AS (
    SELECT
        d.full_date,
        f.value,
        LAG(f.value) OVER (ORDER BY d.full_date) AS prev_value
    FROM fact_indicator f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.indicator_code = 'V39079'
)
SELECT
    full_date,
    prev_value,
    value            AS new_value,
    value - prev_value AS change
FROM rate
WHERE prev_value IS NOT NULL
  AND value <> prev_value
ORDER BY full_date;

-- Q6 (US-3): year-over-year CPI change
WITH cpi AS (
    SELECT
        d.full_date,
        f.value,
        LAG(f.value, 12) OVER (ORDER BY d.full_date) AS value_year_ago
    FROM fact_indicator f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.indicator_code = 'V41690973'
)
SELECT TOP 24
    full_date,
    value                                                        AS cpi,
    value_year_ago,
    ROUND((value - value_year_ago) / value_year_ago * 100.0, 2)  AS yoy_pct
FROM cpi
WHERE value_year_ago IS NOT NULL
ORDER BY full_date DESC;

-- Q7 (US-5): all indicators side by side, one row per month
SELECT
    d.year,
    d.month,
    ROUND(AVG(CASE WHEN f.indicator_code = 'V39079'                THEN f.value END), 3) AS policy_rate,
    ROUND(AVG(CASE WHEN f.indicator_code = 'FXUSDCAD'              THEN f.value END), 4) AS usd_cad,
    ROUND(AVG(CASE WHEN f.indicator_code = 'BD.CDN.10YR.DQ.YLD'    THEN f.value END), 3) AS yield_10yr,
    ROUND(AVG(CASE WHEN f.indicator_code = 'V41690973'             THEN f.value END), 1) AS cpi_index,
    ROUND(AVG(CASE WHEN f.indicator_code = 'STATIC_ATABLE_V35014A' THEN f.value END), 1) AS hourly_earnings_pct
FROM fact_indicator f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.full_date >= '2025-09-01'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Q8 (US-4): freshness of each indicator
SELECT
    i.indicator_name,
    i.frequency,
    MAX(d.full_date) AS latest_date,
    DATEDIFF(day, MAX(d.full_date), CAST(GETDATE() AS DATE)) AS days_old
FROM fact_indicator f
JOIN dim_date d      ON f.date_key = d.date_key
JOIN dim_indicator i ON f.indicator_code = i.indicator_code
GROUP BY i.indicator_name, i.frequency
ORDER BY days_old DESC;