with deliveries as (
    select * from {{ ref('stg_deliveries') }}
)

select
    match_id,
    innings_no,
    batting_team_id,
    bowling_team_id,
    sum(total_runs) as total_runs,
    sum(case when is_wicket then 1 else 0 end) as wickets,
    count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) as legal_balls,
    round(count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) / 6.0, 1) as overs,
    case
        when count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) > 0
        then round(sum(total_runs) * 6.0 / count(case when extra_runs = 0 or dismissal_kind is not null then 1 end), 2)
        else 0
    end as run_rate,
    sum(extra_runs) as extras
from deliveries
group by match_id, innings_no, batting_team_id, bowling_team_id
