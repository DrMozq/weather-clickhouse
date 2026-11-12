SELECT city, min(ts) AS first_ts, max(ts) AS last_ts,
       count() AS hours,
       dateDiff('hour', min(ts), max(ts)) + 1 AS expected
FROM weather.weather_hourly FINAL
GROUP BY city
HAVING hours != expected
