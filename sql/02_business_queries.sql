-- =============================================================================
-- 02_business_queries.sql
-- Business questions answered on top of the star schema.
-- Each query starts with "-- name: <id>" so src/analysis.py can run them one by one.
-- =============================================================================

-- name: kpis_by_hotel
-- Headline KPIs per hotel
SELECT
    h.hotel_name                                                AS hotel,
    COUNT(*)                                                    AS bookings,
    ROUND(100.0 * AVG(f.is_canceled), 1)                        AS cancellation_rate_pct,
    ROUND(SUM(f.revenue) / 1e6, 2)                              AS realised_revenue_m,
    ROUND(SUM(f.lost_revenue) / 1e6, 2)                         AS lost_revenue_m,
    ROUND(AVG(f.adr) FILTER (WHERE f.is_canceled = 0), 2)       AS avg_adr,
    ROUND(AVG(f.total_nights) FILTER (WHERE f.is_canceled = 0), 2) AS avg_nights,
    ROUND(AVG(f.lead_time), 0)                                  AS avg_lead_time_days
FROM fact_bookings f
JOIN dim_hotel h USING (hotel_key)
GROUP BY h.hotel_name
ORDER BY bookings DESC;

-- name: cancellation_by_lead_time
-- The earlier a guest books, the more likely they cancel
SELECT
    lead_time_bucket,
    COUNT(*)                                AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1)      AS cancellation_rate_pct
FROM fact_bookings
GROUP BY lead_time_bucket
ORDER BY MIN(lead_time);

-- name: cancellation_by_deposit
-- Deposit policy vs cancellations
SELECT
    deposit_type,
    COUNT(*)                                AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1)      AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 0)                AS avg_lead_time_days
FROM fact_bookings
GROUP BY deposit_type
ORDER BY bookings DESC;

-- name: segment_performance
-- Market segment performance, ranked by realised revenue
SELECT
    c.market_segment,
    COUNT(*)                                                     AS bookings,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)           AS share_of_bookings_pct,
    ROUND(100.0 * AVG(f.is_canceled), 1)                         AS cancellation_rate_pct,
    ROUND(AVG(f.adr) FILTER (WHERE f.is_canceled = 0), 2)        AS avg_adr,
    ROUND(SUM(f.revenue) / 1e3, 0)                               AS revenue_k,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC)                   AS revenue_rank
FROM fact_bookings f
JOIN dim_channel c USING (channel_key)
GROUP BY c.market_segment
ORDER BY revenue_rank;

-- name: top_countries_pareto
-- Top 10 source markets and cumulative share of revenue (Pareto analysis)
WITH by_country AS (
    SELECT d.country_name, SUM(f.revenue) AS revenue, COUNT(*) AS bookings,
           AVG(f.is_canceled) AS cancel_rate
    FROM fact_bookings f
    JOIN dim_country d USING (country_key)
    GROUP BY d.country_name
)
SELECT
    country_name,
    bookings,
    ROUND(100.0 * cancel_rate, 1)                                            AS cancellation_rate_pct,
    ROUND(revenue / 1e3, 0)                                                  AS revenue_k,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 1)                         AS revenue_share_pct,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 1) AS cumulative_share_pct
FROM by_country
ORDER BY revenue DESC
LIMIT 10;

-- name: seasonality_adr
-- Average daily rate by month and hotel type (price seasonality)
SELECT
    d.month,
    d.month_short                                                                  AS month_name,
    ROUND(AVG(f.adr) FILTER (WHERE h.hotel_type = 'City'   AND f.is_canceled = 0), 2) AS city_adr,
    ROUND(AVG(f.adr) FILTER (WHERE h.hotel_type = 'Resort' AND f.is_canceled = 0), 2) AS resort_adr
FROM fact_bookings f
JOIN dim_date  d ON d.date_key = f.arrival_date_key
JOIN dim_hotel h USING (hotel_key)
GROUP BY d.month, d.month_short
ORDER BY d.month;

-- name: monthly_revenue_yoy
-- Monthly realised revenue with year-over-year growth (window function LAG)
WITH monthly AS (
    SELECT d.year, d.month, d.year_month, SUM(f.revenue) AS revenue
    FROM fact_bookings f
    JOIN dim_date d ON d.date_key = f.arrival_date_key
    GROUP BY d.year, d.month, d.year_month
)
SELECT
    year_month,
    ROUND(revenue / 1e3, 0)                                                   AS revenue_k,
    ROUND(LAG(revenue) OVER (PARTITION BY month ORDER BY year) / 1e3, 0)      AS revenue_prev_year_k,
    ROUND(100.0 * (revenue / LAG(revenue) OVER (PARTITION BY month ORDER BY year) - 1), 1) AS yoy_growth_pct
FROM monthly
ORDER BY year_month;

-- name: repeat_vs_new
-- Loyalty: repeat guests vs new guests
SELECT
    cu.guest_status,
    COUNT(*)                                         AS bookings,
    ROUND(100.0 * AVG(f.is_canceled), 1)             AS cancellation_rate_pct,
    ROUND(AVG(f.adr) FILTER (WHERE f.is_canceled = 0), 2) AS avg_adr,
    ROUND(AVG(f.total_of_special_requests), 2)       AS avg_special_requests
FROM fact_bookings f
JOIN dim_customer cu USING (customer_key)
GROUP BY cu.guest_status
ORDER BY bookings DESC;

-- name: special_requests_effect
-- Engagement signal: guests with special requests cancel far less
SELECT
    LEAST(total_of_special_requests, 3)              AS special_requests,   -- 3 = "3 or more"
    COUNT(*)                                         AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1)               AS cancellation_rate_pct
FROM fact_bookings
GROUP BY 1
ORDER BY 1;
