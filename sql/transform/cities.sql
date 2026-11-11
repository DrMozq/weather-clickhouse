INSERT INTO weather.cities
    (city, geonames_id, region, population, latitude, longitude, elevation, timezone, loaded_at)
SELECT
    city,
    argMax(id,         rank_key),
    argMax(admin1,     rank_key),
    argMax(population, rank_key),
    argMax(latitude,   rank_key),
    argMax(longitude,  rank_key),
    argMax(elevation,  rank_key),
    argMax(timezone,   rank_key),
    {run_ts:DateTime('UTC')}
FROM (
    SELECT *, (coalesce(population, 0), id) AS rank_key
    FROM weather.stg_geocoding
    WHERE loaded_at = {run_ts:DateTime('UTC')}
      AND country_code = 'RU'
      AND replaceAll(lowerUTF8(name), 'ё', 'е') = replaceAll(lowerUTF8(search_name), 'ё', 'е')
)
GROUP BY city
