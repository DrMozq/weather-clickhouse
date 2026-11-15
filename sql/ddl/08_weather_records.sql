CREATE VIEW IF NOT EXISTS weather.weather_records AS
SELECT
    city,
    argMin(date, temp_min) AS coldest_day,
    min(temp_min) AS coldest_temp,
    argMax(date, temp_max) AS hottest_day,
    max(temp_max) AS hottest_temp,
    argMax(date, precipitation_sum) AS wettest_day,
    max(precipitation_sum) AS max_precipitation
FROM weather.weather_daily FINAL
GROUP BY city
