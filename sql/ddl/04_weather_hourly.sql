CREATE TABLE IF NOT EXISTS weather.weather_hourly
(
    city                    LowCardinality(String),
    ts                      DateTime('UTC'),
    temperature_2m          Nullable(Float32),
    apparent_temperature    Nullable(Float32),
    relative_humidity_2m    Nullable(UInt8),
    precipitation           Nullable(Float32),
    snowfall                Nullable(Float32),
    wind_speed_10m          Nullable(Float32),
    pressure_msl            Nullable(Float32),
    weather_code            Nullable(UInt8),
    loaded_at               DateTime('UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(loaded_at)
PARTITION BY toYear(ts)
ORDER BY (city, ts);
