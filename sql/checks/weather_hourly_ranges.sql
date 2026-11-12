SELECT city, ts, temperature_2m, apparent_temperature, relative_humidity_2m,
       precipitation, snowfall, wind_speed_10m, pressure_msl
FROM weather.weather_hourly
WHERE temperature_2m NOT BETWEEN -70 AND 50
   OR apparent_temperature NOT BETWEEN -70 AND 50
   OR relative_humidity_2m NOT BETWEEN 0 AND 100
   OR precipitation < 0
   OR snowfall < 0
   OR wind_speed_10m NOT BETWEEN 0 AND 200
   OR pressure_msl NOT BETWEEN 850 AND 1100
LIMIT 100
