CREATE TABLE IF NOT EXISTS weather.stg_open_meteo
(
    city                            LowCardinality(String),
    start_date                      Date,
    end_date                        Date,
    latitude                        Float64,
    longitude                       Float64,
    elevation                       Float32,
    hourly_units                    Map(String, String),
    hourly_time                     Array(String),
    hourly_temperature_2m           Array(Nullable(Float32)),
    hourly_apparent_temperature     Array(Nullable(Float32)),
    hourly_relative_humidity_2m     Array(Nullable(UInt8)),
    hourly_precipitation            Array(Nullable(Float32)),
    hourly_snowfall                 Array(Nullable(Float32)),
    hourly_wind_speed_10m           Array(Nullable(Float32)),
    hourly_pressure_msl             Array(Nullable(Float32)),
    hourly_weather_code             Array(Nullable(UInt8)),
    loaded_at                       DateTime('UTC') DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(loaded_at)
ORDER BY (city, start_date, loaded_at);
