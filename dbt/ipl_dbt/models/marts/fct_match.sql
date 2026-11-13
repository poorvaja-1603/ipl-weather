with matches as (
    select * from {{ ref('stg_matches') }}
),

innings as (
    select * from {{ ref('int_innings_totals') }}
),

weather as (
    select * from {{ ref('int_match_weather') }}
),

inn1 as (
    select
        match_id,
        batting_team_id as first_innings_team_id,
        total_runs as first_innings_runs,
        wickets as first_innings_wickets
    from innings
    where innings_no = 1
),

inn2 as (
    select
        match_id,
        batting_team_id as second_innings_team_id,
        total_runs as second_innings_runs,
        wickets as second_innings_wickets
    from innings
    where innings_no = 2
)

select
    m.match_id,
    m.season_year,
    m.match_date,
    m.venue_id,
    m.team1_id,
    m.team2_id,
    m.toss_winner_id,
    m.toss_decision,
    m.winner_id,
    m.result_type,
    m.result_margin,
    m.player_of_match,
    m.dl_applied,
    i1.first_innings_team_id,
    i1.first_innings_runs,
    i1.first_innings_wickets,
    i2.second_innings_runs,
    i2.second_innings_wickets,
    case
        when m.result_type = 'no_result' then null
        when m.winner_id = i2.second_innings_team_id then true
        else false
    end as chasing_team_won,
    w.avg_temp_c,
    w.avg_humidity_pct,
    w.avg_dew_point_c,
    w.total_precip_mm,
    w.avg_wind_kmh,
    w.dew_spread_c,
    case
        when w.avg_humidity_pct < 50 then 'low'
        when w.avg_humidity_pct between 50 and 70 then 'medium'
        when w.avg_humidity_pct > 70 then 'high'
        else null
    end as humidity_band,
    case
        when w.avg_temp_c < 25 then 'cool'
        when w.avg_temp_c between 25 and 32 then 'warm'
        when w.avg_temp_c > 32 then 'hot'
        else null
    end as temp_band,
    case
        when w.dew_spread_c <= 3 then 'high'
        when w.dew_spread_c <= 6 then 'medium'
        when w.dew_spread_c > 6 then 'low'
        else null
    end as dew_risk_band
from matches m
left join inn1 i1 on m.match_id = i1.match_id
left join inn2 i2 on m.match_id = i2.match_id
left join weather w on m.match_id = w.match_id
