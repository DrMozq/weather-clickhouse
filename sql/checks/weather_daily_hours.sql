SELECT daily_hours, hourly_rows
FROM (
    SELECT
        (SELECT sum(hours) FROM weather.weather_daily FINAL) AS daily_hours,
        (SELECT count() FROM weather.weather_hourly FINAL) AS hourly_rows
)
WHERE daily_hours != hourly_rows
