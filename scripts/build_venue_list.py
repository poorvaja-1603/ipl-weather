import sys
import pandas as pd

def extract_venues(matches_csv_path: str):
    df = pd.read_csv(matches_csv_path)
    venue_col = None
    for col in ['venue', 'Venue', 'VENUE']:
        if col in df.columns:
            venue_col = col
            break
            
    if not venue_col:
        print("Error: Could not find venue column in CSV.", file=sys.stderr)
        return
        
    counts = df[venue_col].value_counts().reset_index()
    counts.columns = ['raw_venue_name', 'match_count']
    print(counts.to_string(index=False))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python build_venue_list.py <path_to_matches.csv>")
        sys.exit(1)
    extract_venues(sys.argv[1])
