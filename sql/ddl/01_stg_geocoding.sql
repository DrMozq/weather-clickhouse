CREATE TABLE IF NOT EXISTS weather.stg_geocoding
(
    city            LowCardinality(String),
    id              UInt32,
    name            String,
    latitude        Float64,
    longitude       Float64,
    elevation       Nullable(Float32),
    feature_code    LowCardinality(String),
    country_code    LowCardinality(String),
    admin1_id       Nullable(UInt32),
    timezone        LowCardinality(String),
    population      Nullable(UInt32),
    country_id      UInt32,
    country         LowCardinality(String),
    admin1          Nullable(String),
    loaded_at       DateTime('UTC') DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (city, loaded_at);
