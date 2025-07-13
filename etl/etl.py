import wearipedia
import base64
import hashlib
import html
import json
import os
import re
import urllib.parse
import requests
# import matplotlib.pyplot as plt
import pandas as pd
# from sklearn.covariance import EllipticEnvelope
# import seaborn as sns
from scipy import stats
from scipy.ndimage import gaussian_filter
import numpy as np
import os
access_token = ""

def fetch_data(start_date, end_date):
  params = {"seed": 100, "start_date": start_date , "end_date": end_date }

  device = wearipedia.get_device("fitbit/fitbit_charge_6")

  synthetic = os.getenv("IS_SYNTHETIC")
  if not synthetic:
    # If the data is not synthetic, authenticate using the access token
    device.authenticate(access_token)

  br = device.get_data("intraday_breath_rate", params)
  azm = device.get_data("intraday_active_zone_minute", params)
  activity = device.get_data("intraday_activity", params)
  hr = device.get_data("intraday_heart_rate", params)
  hrv = device.get_data("intraday_hrv", params)
  spo2 = device.get_data("intraday_spo2", params)
  
  return br, azm, activity, hr, hrv, spo2 

def transform_br(br_instance):

  record = br_instance['br'][0]
  date = br_instance['br'][0]['dateTime']
  sleep_summary = record['value']
  deep_sleep_br = sleep_summary['deepSleepSummary']['breathingRate']
  rem_sleep_br = sleep_summary['remSleepSummary']['breathingRate']
  light_sleep_br = sleep_summary['lightSleepSummary']['breathingRate']
  full_sleep_br  = sleep_summary['fullSleepSummary']['breathingRate']
  return deep_sleep_br, rem_sleep_br, light_sleep_br, full_sleep_br, date

def transform_hr(hr_instance):

  date = hr_instance['heart_rate_day'][0]['activities-heart'][0]['dateTime']
  hr_data = hr_instance['activities-heart-intraday']['dataset']
  #we can probably return a list of tuples for insertion here
  return date, hr_data

def transform_hrv(hrv_instance):
  hrv_data = hrv_instance['hrv']
  return hrv_data

def transform_spo2(spo2_instance):
  dateTime = spo2_instance['dateTime']
  spo2_data = spo2_instance['minutes']
  return spo2_data

def transform_azm(): 
  pass


def transform_activity(activity_instance): 
  dateTime = activity_instance['dateTime']
  activity = activity_instance['value']
  return dateTime, activity


def connect_db():
  pass

def load():
  pass


if __name__ == "__main__" :
  br,azm, activity, hr, hrv, spo2 = fetch_data(os.getenv("START_DATE"), os.getenv("END_DATE"))
  

