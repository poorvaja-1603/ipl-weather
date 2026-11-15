import json
import urllib.request
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

data = json.load(open('secrets/airbyte-sa.json'))
creds = service_account.Credentials.from_service_account_info(data)
client = bigquery.Client(project='ipl-weather-analytics', credentials=creds, location='US')

key = '078082a9-0b47-430d-bf9d-c5b6c3ab31de'
url = f"https://api.cricapi.com/v1/matches?apikey={key}&offset=0"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    matches = res.get('data', [])

# Flatten matches into records
records = []
for m in matches:
    teams = m.get('teams', [])
    team1 = teams[0] if len(teams) > 0 else None
    team2 = teams[1] if len(teams) > 1 else None
    records.append({
        'match_id': m.get('id'),
        'match_name': m.get('name'),
        'match_type': m.get('matchType'),
        'status': m.get('status'),
        'venue': m.get('venue'),
        'match_date': m.get('date'),
        'date_time_gmt': m.get('dateTimeGMT'),
        'team1': team1,
        'team2': team2,
        'series_id': m.get('series_id')
    })

df = pd.DataFrame(records)
table_id = 'ipl-weather-analytics.raw.matches'
job_config = bigquery.LoadJobConfig(write_disposition='WRITE_TRUNCATE')
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
print(f"SUCCESS! Loaded {len(df)} live match records into {table_id}")
