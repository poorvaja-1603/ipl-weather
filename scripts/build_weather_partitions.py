import json
import sys
import pandas as pd
from datetime import datetime, timedelta

def generate_partitions(matches_csv_path: str, venue_map_csv_path: str, output_json_path: str):
    matches_df = pd.read_csv(matches_csv_path)
    venue_df = pd.read_csv(venue_map_csv_path)

    venue_lookup = dict(zip(venue_df['raw_venue_name'], venue_df['venue_id']))
    coords_lookup = venue_df.set_index('venue_id')[['latitude', 'longitude']].drop_duplicates().to_dict('index')

    venue_col = 'venue' if 'venue' in matches_df.columns else 'Venue'
    date_col = 'date' if 'date' in matches_df.columns else 'Date'

    matches_df['parsed_date'] = pd.to_datetime(matches_df[date_col], errors='coerce')
    matches_df['season_year'] = matches_df['parsed_date'].dt.year
    matches_df['venue_id'] = matches_df[venue_col].map(venue_lookup)

    partitions = []
    grouped = matches_df.groupby(['venue_id', 'season_year'])
    for (v_id, year), group in grouped:
        if pd.isna(v_id) or pd.isna(year):
            continue
        min_date = (group['parsed_date'].min() - timedelta(days=1)).strftime('%Y-%m-%d')
        max_date = (group['parsed_date'].max() + timedelta(days=1)).strftime('%Y-%m-%d')
        coords = coords_lookup.get(v_id, {})
        partitions.append({
            'venue_id': v_id,
            'latitude': coords.get('latitude'),
            'longitude': coords.get('longitude'),
            'start_date': min_date,
            'end_date': max_date
        })

    with open(output_json_path, 'w') as f:
        json.dump(partitions, f, indent=2)

    print(f"Generated {len(partitions)} weather partitions in {output_json_path}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python build_weather_partitions.py <matches.csv> <venue_map.csv> <output.json>")
        sys.exit(1)
    generate_partitions(sys.argv[1], sys.argv[2], sys.argv[3])
