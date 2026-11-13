# IPL Marts Schema Context

## Available Tables in `IPL_DB.MARTS`

### 1. `IPL_DB.MARTS.DIM_TEAM`
- **team_id** (VARCHAR): Primary key for each IPL team.
- **team_name** (VARCHAR): Normalized official team name.
- **short_name** (VARCHAR): Short team abbreviation.

### 2. `IPL_DB.MARTS.DIM_VENUE`
- **venue_id** (VARCHAR): Primary key for each venue.
- **venue_name** (VARCHAR): Standardized official venue name.
- **city** (VARCHAR): City location.
- **country** (VARCHAR): Country location.
- **latitude** (FLOAT): Latitude coordinate.
- **longitude** (FLOAT): Longitude coordinate.

### 3. `IPL_DB.MARTS.FCT_MATCH`
- **match_id** (INT): Unique match ID.
- **season_year** (INT): Year of IPL season.
- **match_date** (DATE): Date of match.
- **venue_id** (VARCHAR): Foreign key to dim_venue.
- **team1_id**, **team2_id** (VARCHAR): Competing teams.
- **toss_winner_id** (VARCHAR), **toss_decision** ('bat'/'field').
- **winner_id** (VARCHAR): Winning team ID.
- **result_type** ('runs', 'wickets', 'tie', 'no_result').
- **result_margin** (INT).
- **first_innings_runs**, **second_innings_runs** (INT).
- **chasing_team_won** (BOOLEAN): True if chasing team won, null for no_result.
- **avg_temp_c** (FLOAT): Match average temperature in Celsius.
- **avg_humidity_pct** (FLOAT): Match average relative humidity (0-100).
- **avg_dew_point_c** (FLOAT): Match average dew point in Celsius.
- **dew_spread_c** (FLOAT): Temperature minus dew point.
- **humidity_band** ('low', 'medium', 'high').
- **temp_band** ('cool', 'warm', 'hot').
- **dew_risk_band** ('high', 'medium', 'low').

### 4. `IPL_DB.MARTS.FCT_INNINGS`
- **match_id** (INT), **innings_no** (INT), **batting_team_id** (VARCHAR), **bowling_team_id** (VARCHAR).
- **total_runs** (INT), **wickets** (INT), **overs** (FLOAT), **run_rate** (FLOAT), **extras** (INT).

### 5. `IPL_DB.MARTS.MART_VENUE_STATS`
- **venue_id** (VARCHAR), **venue_name** (VARCHAR), **matches_played** (INT).
- **avg_first_innings_runs** (FLOAT), **chase_win_pct** (FLOAT), **bat_first_win_pct** (FLOAT), **toss_winner_match_win_pct** (FLOAT).

### 6. `IPL_DB.MARTS.MART_WEATHER_IMPACT`
- **humidity_band** (VARCHAR), **temp_band** (VARCHAR), **dew_risk_band** (VARCHAR).
- **matches** (INT), **avg_first_innings_runs** (FLOAT), **avg_second_innings_runs** (FLOAT), **chase_win_pct** (FLOAT).

### 7. `IPL_DB.MARTS.MART_TEAM_SEASON`
- **team_id** (VARCHAR), **team_name** (VARCHAR), **season_year** (INT).
- **matches** (INT), **wins** (INT), **win_pct** (FLOAT), **avg_runs_scored** (FLOAT), **avg_runs_conceded** (FLOAT).

### 8. `IPL_DB.MARTS.MART_BATTER_SEASON`
- **batter** (VARCHAR), **season_year** (INT), **matches** (INT), **runs** (INT), **balls_faced** (INT), **strike_rate** (FLOAT), **fours** (INT), **sixes** (INT), **dismissals** (INT).

### 9. `IPL_DB.MARTS.MART_BOWLER_SEASON`
- **bowler** (VARCHAR), **season_year** (INT), **balls_bowled** (INT), **overs** (FLOAT), **runs_conceded** (INT), **wickets** (INT), **economy** (FLOAT).

### 10. `IPL_DB.MARTS.MART_BATTER_WEATHER`
- **batter** (VARCHAR), **humidity_band** (VARCHAR), **balls_faced** (INT), **runs** (INT), **strike_rate** (FLOAT).
