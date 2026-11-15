CREATE VIEW IF NOT EXISTS weather.weather_anomalies AS
SELECT
    city,
    month,
    month_temp_avg AS temp_avg,
    avg(month_temp_avg) OVER w AS temp_norm,
    month_temp_avg - temp_norm AS temp_anomaly,
    month_precipitation AS precipitation,
    avg(month_precipitation) OVER w AS precipitation_norm,
    month_precipitation / precipitation_norm AS precipitation_ratio,
    count() OVER w AS years
FROM weather.weather_monthly
WHERE days = toDayOfMonth(toLastDayOfMonth(month))
WINDOW w AS (PARTITION BY city, toMonth(month))
