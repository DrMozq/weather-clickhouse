SELECT DISTINCT city
FROM weather.stg_geocoding
WHERE loaded_at = (SELECT max(loaded_at) FROM weather.stg_geocoding)
  AND city NOT IN (
      SELECT city FROM weather.cities
      WHERE loaded_at = (SELECT max(loaded_at) FROM weather.stg_geocoding)
  )
