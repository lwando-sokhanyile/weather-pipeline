CREATE TABLE IF NOT EXISTS weather_data (
    id               BIGSERIAL PRIMARY KEY,
    city             VARCHAR(100) NOT NULL,
    date             DATE NOT NULL,
    temp_max_c       DOUBLE PRECISION NOT NULL,
    temp_min_c       DOUBLE PRECISION NOT NULL,
    precipitation_mm DOUBLE PRECISION NOT NULL,
    windspeed_kmh    DOUBLE PRECISION NOT NULL,
    weathercode      INTEGER NOT NULL,
    ingested_at      TIMESTAMPTZ NOT NULL,
    temp_range_c     DOUBLE PRECISION NOT NULL,

    CONSTRAINT uq_weather_city_date UNIQUE (city, date)
);

CREATE INDEX IF NOT EXISTS idx_weather_date
    ON weather_data (date);

CREATE INDEX IF NOT EXISTS idx_weather_city
    ON weather_data (city);
