CREATE TABLE IF NOT EXISTS weather.cities
(
    city            LowCardinality(String),
    geonames_id     UInt32,
    region          Nullable(String),
    population      Nullable(UInt32),
    latitude        Float64,
    longitude       Float64,
    elevation       Nullable(Float32),
    timezone        LowCardinality(String),
    loaded_at       DateTime('UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY city;
