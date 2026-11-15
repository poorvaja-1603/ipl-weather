# IPL Marts Schema Context

## Table: `ipl-weather-analytics.marts.dim_team`

One row per normalized IPL franchise.

| Column | Type | Description |
|---|---|---|
| `short_name` | `UNKNOWN` | Short label used for the franchise. |
| `team_id` | `UNKNOWN` | Stable identifier for the franchise across its name changes. |
| `team_name` | `UNKNOWN` | Current standardized name of the franchise. |

## Table: `ipl-weather-analytics.marts.dim_venue`

One row per normalized cricket ground and its location.

| Column | Type | Description |
|---|---|---|
| `city` | `UNKNOWN` | City where the ground is located. |
| `country` | `UNKNOWN` | Country where the ground is located. |
| `latitude` | `UNKNOWN` | Latitude used to retrieve weather observations. |
| `longitude` | `UNKNOWN` | Longitude used to retrieve weather observations. |
| `venue_id` | `UNKNOWN` | Stable identifier for the ground. |
| `venue_name` | `UNKNOWN` | Standardized name of the ground. |

## Table: `ipl-weather-analytics.marts.fct_innings`

One row per match and regular innings with batting totals and legal-ball rates.

| Column | Type | Description |
|---|---|---|
| `batting_team_id` | `UNKNOWN` | Team batting in this innings. |
| `bowling_team_id` | `UNKNOWN` | Team bowling in this innings. |
| `extras` | `UNKNOWN` | Total extras conceded in the innings. |
| `innings_no` | `UNKNOWN` | Regular innings number, either one or two. |
| `match_id` | `UNKNOWN` | Match containing the innings. |
| `overs` | `UNKNOWN` | Legal deliveries divided by six, rounded to one decimal place. |
| `run_rate` | `UNKNOWN` | Runs per six legal deliveries. |
| `total_runs` | `UNKNOWN` | Batter runs plus all recorded extras in the innings. |
| `wickets` | `UNKNOWN` | Number of recorded wickets in the innings. |

## Table: `ipl-weather-analytics.marts.fct_match`

One row per IPL match, including innings summaries and venue weather features.

| Column | Type | Description |
|---|---|---|
| `avg_dew_point_c` | `UNKNOWN` | Average dew point in degrees Celsius in the three-hour assumed match window. |
| `avg_humidity_pct` | `UNKNOWN` | Average relative humidity percentage in the three-hour assumed match window. |
| `avg_temp_c` | `UNKNOWN` | Average air temperature in degrees Celsius in the three-hour assumed match window. |
| `avg_wind_kmh` | `UNKNOWN` | Average wind speed in kilometers per hour in the three-hour assumed match window. |
| `chasing_team_won` | `UNKNOWN` | True when the team batting second won, false when it lost, and null when there was no result. |
| `dew_risk_band` | `UNKNOWN` | Proxy for dew risk based on dew spread: high at 3 degrees or less, medium up to 6, otherwise low. |
| `dew_spread_c` | `UNKNOWN` | Average air temperature minus average dew point in degrees Celsius. |
| `dl_applied` | `UNKNOWN` | Whether a Duckworth-Lewis method was recorded. |
| `first_innings_runs` | `UNKNOWN` | Runs scored in regular innings one. |
| `first_innings_team_id` | `UNKNOWN` | Team that batted in regular innings one. |
| `first_innings_wickets` | `UNKNOWN` | Wickets lost in regular innings one. |
| `humidity_band` | `UNKNOWN` | Low below 50 percent, medium from 50 through 70 percent, or high above 70 percent. |
| `match_date` | `UNKNOWN` | Local calendar date on which the match began. |
| `match_id` | `UNKNOWN` | Unique identifier for the match. |
| `player_of_match` | `UNKNOWN` | Cricsheet's player of the match name. |
| `result_margin` | `UNKNOWN` | Number of runs or wickets in the result, or zero when unavailable. |
| `result_type` | `UNKNOWN` | Normalized result category, such as runs, wickets, tie, or no result. |
| `season_year` | `UNKNOWN` | Calendar year extracted from the match date. |
| `second_innings_runs` | `UNKNOWN` | Runs scored in regular innings two. |
| `second_innings_wickets` | `UNKNOWN` | Wickets lost in regular innings two. |
| `team1_id` | `UNKNOWN` | First team listed in the Cricsheet match information. |
| `team2_id` | `UNKNOWN` | Second team listed in the Cricsheet match information. |
| `temp_band` | `UNKNOWN` | Cool below 25 degrees Celsius, warm from 25 through 32, or hot above 32. |
| `toss_decision` | `UNKNOWN` | Whether the toss winner chose to bat or field. |
| `toss_winner_id` | `UNKNOWN` | Team that won the toss. |
| `total_precip_mm` | `UNKNOWN` | Total precipitation in millimeters in the three-hour assumed match window. |
| `venue_id` | `UNKNOWN` | Ground where the match was played. |
| `winner_id` | `UNKNOWN` | Match winner, including the eliminator winner for a tied match. |

## Table: `ipl-weather-analytics.marts.mart_batter_season`

Batter runs, legal balls, strike rate, boundaries, and dismissals by season.

| Column | Type | Description |
|---|---|---|
| `balls_faced` | `UNKNOWN` | Legal deliveries faced by the batter. |
| `batter` | `UNKNOWN` | Batter name as provided by Cricsheet. |
| `dismissals` | `UNKNOWN` | Dismissals credited to a bowler, excluding run outs and retired hurt. |
| `fours` | `UNKNOWN` | Deliveries with four batter runs. |
| `matches` | `UNKNOWN` | Distinct regular-innings matches in which the batter appeared. |
| `runs` | `UNKNOWN` | Runs credited to the batter. |
| `season_year` | `UNKNOWN` | Calendar year extracted from the match date. |
| `sixes` | `UNKNOWN` | Deliveries with six batter runs. |
| `strike_rate` | `UNKNOWN` | Batter runs per 100 legal deliveries. |

## Table: `ipl-weather-analytics.marts.mart_batter_weather`

Batter runs and strike rate grouped by humidity band.

| Column | Type | Description |
|---|---|---|
| `balls_faced` | `UNKNOWN` | Legal deliveries faced in the humidity grouping. |
| `batter` | `UNKNOWN` | Batter name as provided by Cricsheet. |
| `humidity_band` | `UNKNOWN` | Humidity grouping for matches in which the batter appeared. |
| `runs` | `UNKNOWN` | Batter runs scored in the humidity grouping. |
| `strike_rate` | `UNKNOWN` | Batter runs per 100 legal deliveries in the humidity grouping. |

## Table: `ipl-weather-analytics.marts.mart_bowler_season`

Bowler legal deliveries, overs, runs conceded, wickets, and economy by season.

| Column | Type | Description |
|---|---|---|
| `balls_bowled` | `UNKNOWN` | Legal deliveries bowled. |
| `bowler` | `UNKNOWN` | Bowler name as provided by Cricsheet. |
| `economy` | `UNKNOWN` | Runs conceded per six legal deliveries. |
| `overs` | `UNKNOWN` | Legal deliveries divided by six, rounded to one decimal place. |
| `runs_conceded` | `UNKNOWN` | Total runs conceded by the bowler's innings deliveries. |
| `season_year` | `UNKNOWN` | Calendar year extracted from the match date. |
| `wickets` | `UNKNOWN` | Bowler-credit wickets, excluding run outs, retired hurt, and obstructing the field. |

## Table: `ipl-weather-analytics.marts.mart_team_season`

Team match counts, win rate, and average runs scored and conceded by season.

| Column | Type | Description |
|---|---|---|
| `avg_runs_conceded` | `UNKNOWN` | Average runs conceded by the team in an innings. |
| `avg_runs_scored` | `UNKNOWN` | Average runs scored by the team in an innings. |
| `matches` | `UNKNOWN` | Matches with a result played by the team in the season. |
| `season_year` | `UNKNOWN` | Calendar year extracted from the season's match dates. |
| `team_id` | `UNKNOWN` | Franchise represented by the seasonal summary. |
| `team_name` | `UNKNOWN` | Standardized franchise name. |
| `win_pct` | `UNKNOWN` | Wins divided by matches with a result, multiplied by 100. |
| `wins` | `UNKNOWN` | Matches won by the team in the season. |

## Table: `ipl-weather-analytics.marts.mart_venue_stats`

Match counts, first-innings scores, and win percentages by venue.

| Column | Type | Description |
|---|---|---|
| `avg_first_innings_runs` | `UNKNOWN` | Average runs scored in regular innings one. |
| `bat_first_win_pct` | `UNKNOWN` | Percentage of matches with a result won by the team batting first. |
| `chase_win_pct` | `UNKNOWN` | Percentage of matches with a result won by the team batting second. |
| `matches_played` | `UNKNOWN` | Matches with a result at the ground. |
| `toss_winner_match_win_pct` | `UNKNOWN` | Percentage of matches with a result in which the toss-winning team also won the match. |
| `venue_id` | `UNKNOWN` | Ground represented by this venue summary. |
| `venue_name` | `UNKNOWN` | Standardized name of the ground. |

## Table: `ipl-weather-analytics.marts.mart_weather_impact`

Match and scoring summaries by humidity, temperature, and dew-risk bands.

| Column | Type | Description |
|---|---|---|
| `avg_first_innings_runs` | `UNKNOWN` | Average runs in regular innings one. |
| `avg_second_innings_runs` | `UNKNOWN` | Average runs in regular innings two. |
| `chase_win_pct` | `UNKNOWN` | Percentage of matches with a result won by the team batting second. |
| `dew_risk_band` | `UNKNOWN` | Dew-spread proxy grouping for the match weather window. |
| `humidity_band` | `UNKNOWN` | Humidity grouping for the match weather window. |
| `matches` | `UNKNOWN` | Matches with a result in this weather grouping. |
| `temp_band` | `UNKNOWN` | Temperature grouping for the match weather window. |
