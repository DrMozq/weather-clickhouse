INSERT INTO weather.weather_hourly
    (city, ts, temperature_2m, apparent_temperature, relative_humidity_2m,
     precipitation, snowfall, wind_speed_10m, pressure_msl, weather_code, loaded_at)
SELECT
    city,
    parseDateTimeBestEffort(t, 'UTC') AS ts, 
    temperature_2m,
    apparent_temperature,
    relative_humidity_2m,
    precipitation,
    snowfall,
    wind_speed_10m,
    pressure_msl,
    weather_code,
    loaded_at
FROM weather.stg_open_meteo
ARRAY JOIN
    hourly_time AS t,
    hourly_temperature_2m AS temperature_2m,
    hourly_apparent_temperature AS apparent_temperature,
    hourly_relative_humidity_2m AS relative_humidity_2m,
    hourly_precipitation AS precipitation,
    hourly_snowfall AS snowfall,
    hourly_wind_speed_10m AS wind_speed_10m,
    hourly_pressure_msl AS pressure_msl,
    hourly_weather_code AS weather_code
WHERE loaded_at >= (SELECT max(loaded_at) FROM weather.weather_hourly)
