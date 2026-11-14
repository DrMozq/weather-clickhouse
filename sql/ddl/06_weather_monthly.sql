CREATE VIEW IF NOT EXISTS weather.weather_monthly AS
SELECT
    city,
    toStartOfMonth(date) AS month,
    min(temp_min) AS month_temp_min,
    max(temp_max) AS month_temp_max,
    avg(temp_avg) AS month_temp_avg,
    sum(precipitation_sum) AS month_precipitation,
    countIf(temp_min < 0) AS frost_days,
    countIf(temp_max > 25) AS hot_days,
    countIf(precipitation_sum >= 1) AS wet_days,
    count() AS days
FROM weather.weather_daily FINAL
GROUP BY city, month
