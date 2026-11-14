CREATE TABLE IF NOT EXISTS weather.weather_daily
(
    city               LowCardinality(String),
    date               Date,
    temp_min           Nullable(Float32),
    temp_max           Nullable(Float32),
    temp_avg           Nullable(Float32),
    precipitation_sum  Nullable(Float32),
    snowfall_sum       Nullable(Float32),
    wind_max           Nullable(Float32),
    humidity_avg       Nullable(Float32),
    hours              UInt8,
    loaded_at          DateTime('UTC')
)
ENGINE = ReplacingMergeTree(loaded_at)
PARTITION BY toYear(date)
ORDER BY (city, date);
