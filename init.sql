CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS raw_data(
    time TIMESTAMPTZ NOT NULL,
    user_id INTEGER NOT NULL,
    heart_rate INTEGER NULL,
    rmssd_hrv REAL NULL,
    hf_hrv REAL NULL,
    lf_hrv REAL NULL,
    coverage_hrv REAL NULL,
    deep_sleep_br REAL NULL,
    rem_sleep_br REAL NULL,
    light_sleep_br REAL NULL,
    full_sleep_br REAL NULL,
    activity BIGINT NULL,
    spo2 REAL NULL,
    fat_burn_azm INTEGER NULL,
    peak_azm INTEGER NULL,
    cardio_azm INTEGER NULL,
    azm INTEGER NULL
);

SELECT create_hypertable('raw_data', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_user_id_time ON raw_data (user_id, time DESC);