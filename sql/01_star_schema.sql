-- =============================================================================
-- 01_star_schema.sql
-- Builds the analytical star schema from the clean staging table stg_bookings.
--
--   dim_date ─┐
--   dim_hotel ─┤
--   dim_country ─┼── fact_bookings (1 row = 1 booking)
--   dim_channel ─┤
--   dim_customer ─┘
-- =============================================================================

-- ---------------------------------------------------------------- dim_date
CREATE OR REPLACE TABLE dim_date AS
WITH bounds AS (
    SELECT LEAST(MIN(booking_date), MIN(arrival_date)) AS d0,
           MAX(arrival_date)                           AS d1
    FROM stg_bookings
)
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER)        AS date_key,
    CAST(d AS DATE)                               AS full_date,
    year(d)                                       AS year,
    quarter(d)                                    AS quarter,
    'Q' || quarter(d)                             AS quarter_label,
    month(d)                                      AS month,
    strftime(d, '%B')                             AS month_name,
    strftime(d, '%b')                             AS month_short,
    strftime(d, '%Y-%m')                          AS year_month,
    weekofyear(d)                                 AS week_of_year,
    isodow(d)                                     AS day_of_week,       -- 1 = Monday
    strftime(d, '%A')                             AS day_name,
    CASE WHEN isodow(d) IN (6, 7) THEN 1 ELSE 0 END AS is_weekend,
    CASE WHEN month(d) IN (12, 1, 2) THEN 'Winter'
         WHEN month(d) IN (3, 4, 5)  THEN 'Spring'
         WHEN month(d) IN (6, 7, 8)  THEN 'Summer'
         ELSE 'Autumn' END                        AS season
FROM bounds, generate_series(d0, d1, INTERVAL 1 DAY) AS t(d);

-- ---------------------------------------------------------------- dim_hotel
CREATE OR REPLACE TABLE dim_hotel AS
SELECT
    ROW_NUMBER() OVER (ORDER BY hotel)                          AS hotel_key,
    hotel                                                       AS hotel_name,
    CASE WHEN hotel ILIKE '%resort%' THEN 'Resort' ELSE 'City' END AS hotel_type
FROM (SELECT DISTINCT hotel FROM stg_bookings);

-- ---------------------------------------------------------------- dim_country
CREATE OR REPLACE TABLE dim_country AS
SELECT
    ROW_NUMBER() OVER (ORDER BY b.country)          AS country_key,
    b.country                                       AS country_code,
    COALESCE(n.country_name, b.country)             AS country_name,
    CASE WHEN b.country = 'PRT' THEN 'Domestic'
         WHEN b.country = 'UNK' THEN 'Unknown'
         ELSE 'International' END                   AS market
FROM (SELECT DISTINCT country FROM stg_bookings) b
LEFT JOIN stg_country_names n ON n.country_code = b.country;

-- ---------------------------------------------------------------- dim_channel
CREATE OR REPLACE TABLE dim_channel AS
SELECT
    ROW_NUMBER() OVER (ORDER BY market_segment, distribution_channel) AS channel_key,
    market_segment,
    distribution_channel
FROM (SELECT DISTINCT market_segment, distribution_channel FROM stg_bookings);

-- ---------------------------------------------------------------- dim_customer
CREATE OR REPLACE TABLE dim_customer AS
SELECT
    ROW_NUMBER() OVER (ORDER BY customer_type, is_repeated_guest) AS customer_key,
    customer_type,
    is_repeated_guest,
    CASE WHEN is_repeated_guest = 1 THEN 'Repeat guest' ELSE 'New guest' END AS guest_status
FROM (SELECT DISTINCT customer_type, is_repeated_guest FROM stg_bookings);

-- ---------------------------------------------------------------- fact_bookings
CREATE OR REPLACE TABLE fact_bookings AS
SELECT
    s.booking_id,
    CAST(strftime(s.arrival_date, '%Y%m%d') AS INTEGER) AS arrival_date_key,
    CAST(strftime(s.booking_date, '%Y%m%d') AS INTEGER) AS booking_date_key,
    h.hotel_key,
    c.country_key,
    ch.channel_key,
    cu.customer_key,
    -- booking attributes
    s.lead_time,
    s.lead_time_bucket,
    s.lead_time_bucket_order,
    s.deposit_type,
    s.meal,
    s.reserved_room_type,
    s.assigned_room_type,
    s.room_changed,
    s.booking_changes,
    s.days_in_waiting_list,
    s.previous_cancellations,
    s.previous_bookings_not_canceled,
    s.has_agent,
    s.has_company,
    s.required_car_parking_spaces,
    s.total_of_special_requests,
    -- stay
    s.stays_in_weekend_nights,
    s.stays_in_week_nights,
    s.total_nights,
    s.adults,
    s.children,
    s.babies,
    s.total_guests,
    s.is_family,
    -- outcome & money
    s.is_canceled,
    s.reservation_status,
    s.adr,
    s.revenue,
    s.lost_revenue
FROM stg_bookings s
JOIN dim_hotel    h  ON h.hotel_name = s.hotel
JOIN dim_country  c  ON c.country_code = s.country
JOIN dim_channel  ch ON ch.market_segment = s.market_segment
                    AND ch.distribution_channel = s.distribution_channel
JOIN dim_customer cu ON cu.customer_type = s.customer_type
                    AND cu.is_repeated_guest = s.is_repeated_guest;
