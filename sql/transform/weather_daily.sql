INSERT INTO weather.weather_daily
    (city, date, temp_min, temp_max, temp_avg, precipitation_sum, snowfall_sum,
     wind_max, humidity_avg, hours, loaded_at)
WITH
    tz_cities AS (
        SELECT city FROM weather.cities FINAL WHERE timezone = {tz:String}
    ),
    affected AS (
        SELECT DISTINCT city, toDate(ts, {tz:String}) AS date
        FROM weather.weather_hourly
        WHERE city IN tz_cities
          AND loaded_at >= (
              SELECT max(loaded_at) FROM weather.weather_daily WHERE city IN tz_cities
          )
    )
SELECT
    city,
    toDate(ts, {tz:String}) AS date,
    min(temperature_2m) AS temp_min,
    max(temperature_2m) AS temp_max,
    avg(temperature_2m) AS temp_avg,
    sum(precipitation) AS precipitation_sum,
    sum(snowfall) AS snowfall_sum,
    max(wind_speed_10m) AS wind_max,
    avg(relative_humidity_2m) AS humidity_avg,
    count() AS hours,
    max(loaded_at)
FROM weather.weather_hourly FINAL
WHERE city IN tz_cities
  AND (city, date) IN affected
GROUP BY city, date
