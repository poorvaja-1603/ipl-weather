# IPL Marts Schema Context (Google BigQuery)

## Available Tables in `marts` Dataset

### 1. `marts.dim_team`
- **team_id** (STRING): Primary key for each IPL team (e.g. 'CSK', 'MI', 'RCB').
- **team_name** (STRING): Normalized official team name.
- **short_name** (STRING): Short team abbreviation.

### 2. `marts.dim_venue`
- **venue_id** (STRING): Primary key for each venue (e.g. 'wankhede', 'chepauk', 'eden_gardens').
- **venue_name** (STRING): Standardized official venue name.
- **city** (STRING): City location.
- **country** (STRING): Country location.
- **latitude** (FLOAT64): Latitude coordinate.
- **longitude** (FLOAT64): Longitude coordinate.

### 3. `marts.fct_match`
- **match_id** (INT64): Unique match ID.
- **season_year** (INT64): Year of IPL season.
- **match_date** (DATE): Date match occurred.
- **venue_id** (STRING): Foreign key to dim_venue.
- **team1_id**, **team2_id** (STRING): Competing teams.
- **toss_winner_id** (STRING), **toss_decision** ('bat'/'field').
- **winner_id** (STRING): Winning team ID.
- **result_type** ('runs', 'wickets', 'tie', 'no_result').
- **result_margin** (INT64).
- **first_innings_runs**, **second_innings_runs** (INT64).
- **chasing_team_won** (BOOL): True if chasing team won, null for no_result.
- **avg_temp_c** (FLOAT64): Match average temperature in Celsius.
- **avg_humidity_pct** (FLOAT64): Match average relative humidity (0-100).
- **avg_dew_point_c** (FLOAT64): Match average dew point in Celsius.
- **dew_spread_c** (FLOAT64): Temperature minus dew point.
- **humidity_band** ('low', 'medium', 'high').
- **temp_band** ('cool', 'warm', 'hot').
- **dew_risk_band** ('high', 'medium', 'low').

### 4. `marts.fct_innings`
- **match_id** (INT64), **innings_no** (INT64), **batting_team_id** (STRING), **bowling_team_id** (STRING).
- **total_runs** (INT64), **wickets** (INT64), **overs** (FLOAT64), **run_rate** (FLOAT64), **extras** (INT64).

### 5. `marts.mart_venue_stats`
- **venue_id** (STRING), **venue_name** (STRING), **matches_played** (INT64).
- **avg_first_innings_runs** (FLOAT64), **chase_win_pct** (FLOAT64), **bat_first_win_pct** (FLOAT64), **toss_winner_match_win_pct** (FLOAT64).

### 6. `marts.mart_weather_impact`
- **humidity_band** (STRING), **temp_band** (STRING), **dew_risk_band** (STRING).
- **matches** (INT64), **avg_first_innings_runs** (FLOAT64), **avg_second_innings_runs** (FLOAT64), **chase_win_pct** (FLOAT64).

### 7. `marts.mart_team_season`
- **team_id** (STRING), **team_name** (STRING), **season_year** (INT64).
- **matches** (INT64), **wins** (INT64), **win_pct** (FLOAT64), **avg_runs_scored** (FLOAT64), **avg_runs_conceded** (FLOAT64).

### 8. `marts.mart_batter_season`
- **batter** (STRING), **season_year** (INT64), **matches** (INT64), **runs** (INT64), **balls_faced** (INT64), **strike_rate** (FLOAT64), **fours** (INT64), **sixes** (INT64), **dismissals** (INT64).

### 9. `marts.mart_bowler_season`
- **bowler** (STRING), **season_year** (INT64), **balls_bowled** (INT64), **overs** (FLOAT64), **runs_conceded** (INT64), **wickets** (INT64), **economy** (FLOAT64).

### 10. `marts.mart_batter_weather`
- **batter** (STRING), **humidity_band** (STRING), **balls_faced** (INT64), **runs** (INT64), **strike_rate** (FLOAT64).
