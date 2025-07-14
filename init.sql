CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS raw_data(
    time TIMESTAMPTZ NOT NULL,
    user_id INTEGER NOT NULL,
    heart_rate DOUBLE PRECISION NULL,
    rmssd_hrv DOUBLE PRECISION NULL,
    hf_hrv DOUBLE PRECISION NULL,
    lf_hrv DOUBLE PRECISION NULL,
    coverage_hrv DOUBLE PRECISION NULL,
    deep_sleep_br DOUBLE PRECISION NULL,
    rem_sleep_br DOUBLE PRECISION NULL,
    light_sleep_br DOUBLE PRECISION NULL,
    full_sleep_br DOUBLE PRECISION NULL,
    activity BIGINT NULL,
    spo2 DOUBLE PRECISION NULL,
    fat_burn_azm INTEGER NULL,
    peak_azm INTEGER NULL,
    cardio_azm INTEGER NULL,
    azm INTEGER NULL
);

SELECT create_hypertable('raw_data', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_user_id_time ON raw_data (user_id, time DESC);

ALTER TABLE raw_data ADD CONSTRAINT unique_user_time UNIQUE (user_id, time);