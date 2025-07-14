from datetime import datetime, date, timezone
import wearipedia
import os
import pandas as pd
from scipy import stats
from scipy.ndimage import gaussian_filter
import numpy as np
import os
import psycopg2
from datetime import date, timedelta
from dotenv import load_dotenv
access_token = ""
load_dotenv()

user_id = 1 if os.getenv("IS_SYNTHETIC") else os.getenv("CLIENT_ID")


def fetch_data(start_date, end_date):
    params = {"seed": 100, "start_date": start_date, "end_date": end_date}

    device = wearipedia.get_device("fitbit/fitbit_charge_6")

    synthetic = os.getenv("IS_SYNTHETIC")
    if synthetic == "False":
        # If the data is not synthetic, authenticate using the access token
        device.authenticate(access_token)

    br = device.get_data("intraday_breath_rate", params)
    azm = device.get_data("intraday_active_zone_minute", params)
    activity = device.get_data("intraday_activity", params)
    hr = device.get_data("intraday_heart_rate", params)
    hrv = device.get_data("intraday_hrv", params)
    spo2 = device.get_data("intraday_spo2", params)
    return br, azm, activity, hr, hrv, spo2

# function to transform a single instance of br intraday data


def transform_br(br_instance):
    record = br_instance['br'][0]
    date = br_instance['br'][0]['dateTime']
    sleep_summary = record['value']
    deep_sleep_br = sleep_summary['deepSleepSummary']['breathingRate'] if not np.isnan(sleep_summary['deepSleepSummary']['breathingRate']) else None
    rem_sleep_br = sleep_summary['remSleepSummary']['breathingRate'] if not np.isnan(
        sleep_summary['remSleepSummary']['breathingRate']) else None
    light_sleep_br = sleep_summary['lightSleepSummary']['breathingRate'] if not np.isnan(
        sleep_summary['lightSleepSummary']['breathingRate']) else None
    full_sleep_br = sleep_summary['fullSleepSummary']['breathingRate'] if not np.isnan(
        sleep_summary['fullSleepSummary']['breathingRate']) else None
    date = transform_date_year(date)
    record = (date, user_id, None, None, None, None, None, float(deep_sleep_br), float(rem_sleep_br),
              float(light_sleep_br), float(full_sleep_br), None, None, None, None, None, None)
    return record

# function to transform a single instance of hr intraday data


def transform_hr(hr_instance):
    date = hr_instance['heart_rate_day'][0]['activities-heart'][0]['dateTime']
    hr_data = hr_instance['heart_rate_day'][0]['activities-heart-intraday']['dataset']
    final_records = []
    for record_second in hr_data:
        time = record_second['time']
        hr = record_second['value'] if not np.isnan(
            record_second['value']) else None
        final_datetime = transform_date(date + 'T' + time)
        transformed_record = (final_datetime, user_id, float(hr), None, None, None,
                              None, None, None, None, None, None, None, None, None, None, None)
        final_records.append(transformed_record)
    return final_records

# function to transform a single instance of hrv intraday data


def transform_hrv(hrv_instance):
    hrv_data = hrv_instance['hrv'][0]['minutes']
    final_records = []
    for record_second in hrv_data:
        date_time = record_second['minute']
        transformed_datetime = transform_date_ms(date_time)
        rmssd = record_second['value']['rmssd'] if not np.isnan(
            record_second['value']['rmssd']) else None
        coverage = record_second['value']['coverage'] if not np.isnan(
            record_second['value']['coverage']) else None
        hf = record_second['value']['hf'] if not np.isnan(
            record_second['value']['hf']) else None
        lf = record_second['value']['lf'] if not np.isnan(
            record_second['value']['lf']) else None

        final_record = (transformed_datetime, user_id, None, float(rmssd), float(hf), float(lf),
                        float(coverage), None, None, None, None, None, None, None, None, None, None)
        final_records.append(final_record)
    return final_records

# function to transform a single instance of spo2 intraday data


def transform_spo2(spo2_instance):
    spo2_data = spo2_instance['minutes']
    final_records = []
    for record in spo2_data:
        spo2 = record['value'] if not np.isnan(record['value']) else None
        transformed_datetime = transform_date(record['minute'])
        transformed_record = (transformed_datetime, user_id, None, None, None,
                              None, None, None, None, None, None, None, float(spo2), None, None, None, None)
        final_records.append(transformed_record)

    return final_records

# function to transform a single instance of azm intraday data
def transform_azm(azm_instance):
    datetime = azm_instance['activities-active-zone-minutes-intraday'][0]['dateTime']
    azm_data = azm_instance['activities-active-zone-minutes-intraday'][0]['minutes']
    final_records = []
    fatburn_azm = None
    cardio_azm = None
    peak_azm = None
    for azm_record in azm_data:
        minute = azm_record['minute']
        transformed_datetime = transform_date(datetime+'T'+minute)
        value = azm_record['value']
        if 'fatBurnActiveZoneMinutes' in value:
            fatburn_azm = value['fatBurnActiveZoneMinutes'] if not np.isnan(
                value['fatBurnActiveZoneMinutes']) else None
        elif 'cardioActiveZoneMinutes' in value:
            cardio_azm = value['cardioActiveZoneMinutes'] if not np.isnan(
                value['cardioActiveZoneMinutes']) else None
        elif 'peakActiveZoneMinutes' in value:
            peak_azm = value['peakActiveZoneMinutes'] if not np.isnan(
                value['peakActiveZoneMinutes']) else None

        azm = value['activeZoneMinutes'] if not np.isnan(
            value['activeZoneMinutes']) else None

        final_record = (transformed_datetime, user_id, None, None, None, None, None,
                        None, None, None, None, None, None, None if fatburn_azm==None else float(fatburn_azm), None if peak_azm==None else float(peak_azm), None if cardio_azm==None else float(cardio_azm), azm)
        final_records.append(final_record)

    return final_records

# function to transform a single instance of activity intraday data
def transform_activity(activity_instance):
    dateTime = activity_instance['dateTime']
    activity = activity_instance['value']
    transformed_date = transform_date_year(dateTime)
    transformed_record = (transformed_date, user_id, None, None, None, None,
                          None, None, None, None, None, activity, None, None, None, None, None)
    return transformed_record


def transform_date(date_string):
    try:
        dt_naive = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        return dt_naive.replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Error parsing date string: {date_string}")
        return None


def transform_date_ms(date_string):
    try:
        dt_naive = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")
        return dt_naive.replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Error parsing date string: {date_string}")
        return None


def transform_date_year(date_string):
    try:
        dt_naive = datetime.strptime(date_string, "%Y-%m-%d")
        return dt_naive.replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Error parsing date string: {date_string}")
        return None

def upsert_wearable_data(data_rows):
    upsert_sql = """
        INSERT INTO raw_data (
            time, user_id, heart_rate, rmssd_hrv, hf_hrv, lf_hrv, 
            coverage_hrv, deep_sleep_br, rem_sleep_br, light_sleep_br, 
            full_sleep_br, activity, spo2, fat_burn_azm, peak_azm, 
            cardio_azm, azm
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (user_id, time) DO UPDATE SET
            heart_rate = COALESCE(EXCLUDED.heart_rate, raw_data.heart_rate),
            rmssd_hrv = COALESCE(EXCLUDED.rmssd_hrv, raw_data.rmssd_hrv),
            hf_hrv = COALESCE(EXCLUDED.hf_hrv, raw_data.hf_hrv),
            lf_hrv = COALESCE(EXCLUDED.lf_hrv, raw_data.lf_hrv),
            coverage_hrv = COALESCE(EXCLUDED.coverage_hrv, raw_data.coverage_hrv),
            deep_sleep_br = COALESCE(EXCLUDED.deep_sleep_br, raw_data.deep_sleep_br),
            rem_sleep_br = COALESCE(EXCLUDED.rem_sleep_br, raw_data.rem_sleep_br),
            light_sleep_br = COALESCE(EXCLUDED.light_sleep_br, raw_data.light_sleep_br),
            full_sleep_br = COALESCE(EXCLUDED.full_sleep_br, raw_data.full_sleep_br),
            activity = COALESCE(EXCLUDED.activity, raw_data.activity),
            spo2 = COALESCE(EXCLUDED.spo2, raw_data.spo2),
            fat_burn_azm = COALESCE(EXCLUDED.fat_burn_azm, raw_data.fat_burn_azm),
            peak_azm = COALESCE(EXCLUDED.peak_azm, raw_data.peak_azm),
            cardio_azm = COALESCE(EXCLUDED.cardio_azm, raw_data.cardio_azm),
            azm = COALESCE(EXCLUDED.azm, raw_data.azm);
    """

    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        print("Connection to TimescaleDB successful.")

        cursor.executemany(upsert_sql, data_rows)
        conn.commit()
        print(f"Successfully upserted {cursor.rowcount} row(s).")

    except psycopg2.Error as e:
        print(f" Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Connection closed.")


def get_last_processed_date_synthetic(user_id):
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()

        cursor.execute(
            "SELECT MAX(time) FROM raw_data WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()[0]

        if result:
            return result.date()
        return None

    except psycopg2.Error as e:
        print(
            f"Database query error in get_last_processed_date_synthetic: {e}")
        return None
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":

    IS_SYNTHETIC = os.getenv("IS_SYNTHETIC")

    all_records_to_upsert = []

    if IS_SYNTHETIC == "True":
        """
        etl for synthetic data
        """
        SYNTHETIC_START_DATE = date(2024, 1, 1)
        SYNTHETIC_END_DATE = date(2024, 1, 30)

        last_date = get_last_processed_date_synthetic(user_id)
        target_date = (last_date + datetime.timedelta(days=1)
                       ) if last_date else SYNTHETIC_START_DATE

        if target_date > SYNTHETIC_END_DATE:
            print("Synthetic data has already been processed")
        else:
            target_date_str = target_date.strftime("%Y-%m-%d")
            print(
                f"Fetching full synthetic dataset to process data for: {target_date_str}")

            br, azm, activity, hr, hrv, spo2 = fetch_data(
                start_date=target_date_str, end_date=target_date_str)

            daily_br = next((item for item in br if item.get(
                'br') and item['br'][0]['dateTime'] == target_date_str), None)
            daily_azm = next((item for item in azm if item.get('activities-active-zone-minutes-intraday')
                             and item['activities-active-zone-minutes-intraday'][0]['dateTime'] == target_date_str), None)
            daily_activity = next(
                (item for item in activity if item.get('dateTime') == target_date_str), None)
            daily_hr = next((item for item in hr if item.get(
                'heart_rate_day') and item['heart_rate_day'][0]['activities-heart'][0]['dateTime'] == target_date_str), None)
            daily_hrv = next((item for item in hrv if item.get(
                'hrv') and item['hrv'][0]['minutes'][0]['minute'].startswith(target_date_str)), None)
            daily_spo2 = next((item for item in spo2 if item.get(
                'dateTime') == target_date_str), None)

            if daily_br:
                all_records_to_upsert.append(transform_br(daily_br))
            if daily_azm:
                all_records_to_upsert.extend(transform_azm(daily_azm))
            if daily_activity:
                all_records_to_upsert.append(
                    transform_activity(daily_activity))
            if daily_hr:
                all_records_to_upsert.extend(transform_hr(daily_hr))
            if daily_hrv:
                all_records_to_upsert.extend(transform_hrv(daily_hrv))
            if daily_spo2:
                all_records_to_upsert.extend(transform_spo2(daily_spo2))

    else:
        """
        this portion is executed if we're data is not synthetic and we need to do extraction everyday
        """

        target_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"Fetching live data for: {target_date}")
        br, azm, activity, hr, hrv, spo2 = fetch_data(
            start_date=target_date, end_date=target_date)

        if br:
            all_records_to_upsert.append(transform_br(br))
        if azm:
            all_records_to_upsert.extend(transform_azm(azm))
        if activity:
           
            all_records_to_upsert.append(transform_activity(activity))
        if hr:
            all_records_to_upsert.extend(transform_hr(hr))
        if hrv:
            all_records_to_upsert.extend(transform_hrv(hrv))
        if spo2:
            all_records_to_upsert.extend(transform_spo2(spo2))

    if all_records_to_upsert:
        print(
            f"Collected a total of {len(all_records_to_upsert)} records to upsert.")
        upsert_wearable_data(all_records_to_upsert)
    else:
        print("No new data was found for the target date.")
