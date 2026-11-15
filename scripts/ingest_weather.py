import json
import urllib.request
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

data = json.load(open('secrets/airbyte-sa.json'))
creds = service_account.Credentials.from_service_account_info(data)
client = bigquery.Client(project='ipl-weather-analytics', credentials=creds, location='US')

venues = [
    {'venue_id': 'wankhede', 'lat': 18.9389, 'lon': 72.8258},
    {'venue_id': 'chinnaswamy', 'lat': 12.9788, 'lon': 77.5996},
    {'venue_id': 'chepauk', 'lat': 13.0628, 'lon': 80.2793},
    {'venue_id': 'eden_gardens', 'lat': 22.5646, 'lon': 88.3433},
    {'venue_id': 'motera', 'lat': 23.0917, 'lon': 72.5975},
    {'venue_id': 'feroz_shah', 'lat': 28.6378, 'lon': 77.2423},
    {'venue_id': 'uppal', 'lat': 17.4065, 'lon': 78.5505}
]

rows = []
for v in venues:
    lat = v['lat']
    lon = v['lon']
    v_id = v['venue_id']
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-03-22&end_date=2024-05-26&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,wind_speed_10m&timezone=auto"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        hourly = res.get('hourly', {})
        times = hourly.get('time', [])
        for i in range(len(times)):
            rows.append({
                'venue_id': v_id,
                'observed_at': times[i],
                'temperature_c': float(hourly['temperature_2m'][i]) if hourly['temperature_2m'][i] is not None else None,
                'humidity_pct': float(hourly['relative_humidity_2m'][i]) if hourly['relative_humidity_2m'][i] is not None else None,
                'dew_point_c': float(hourly['dew_point_2m'][i]) if hourly['dew_point_2m'][i] is not None else None,
                'precipitation_mm': float(hourly['precipitation'][i]) if hourly['precipitation'][i] is not None else None,
                'wind_kmh': float(hourly['wind_speed_10m'][i]) if hourly['wind_speed_10m'][i] is not None else None
            })

df = pd.DataFrame(rows)
table_id = 'ipl-weather-analytics.raw.weather_hourly'
job_config = bigquery.LoadJobConfig(write_disposition='WRITE_TRUNCATE')
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
print(f"SUCCESS! Loaded {len(df)} weather records into {table_id}")
