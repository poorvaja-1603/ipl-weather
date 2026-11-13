select
    humidity_band,
    temp_band,
    dew_risk_band,
    count(case when result_type != 'no_result' then 1 end) as matches,
    round(avg(first_innings_runs), 2) as avg_first_innings_runs,
    round(avg(second_innings_runs), 2) as avg_second_innings_runs,
    round(100.0 * count(case when chasing_team_won = true then 1 end) / nullif(count(case when result_type != 'no_result' then 1 end), 0), 2) as chase_win_pct
from {{ ref('fct_match') }}
where humidity_band is not null
  and temp_band is not null
  and dew_risk_band is not null
group by humidity_band, temp_band, dew_risk_band
