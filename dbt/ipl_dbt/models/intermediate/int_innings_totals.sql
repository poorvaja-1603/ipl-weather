with deliveries as (
    select *
    from {{ ref('stg_deliveries') }}
    where innings_no in (1, 2)
      and not is_super_over_innings
)

select
    match_id,
    innings_no,
    batting_team_id,
    bowling_team_id,
    sum(total_runs) as total_runs,
    countif(is_wicket and lower(coalesce(dismissal_kind, '')) != 'retired hurt') as wickets,
    countif(is_legal_ball) as legal_balls,
    round(safe_divide(countif(is_legal_ball), 6.0), 1) as overs,
    coalesce(round(safe_divide(sum(total_runs) * 6.0, countif(is_legal_ball)), 2), 0) as run_rate,
    sum(extra_runs) as extras
from deliveries
group by match_id, innings_no, batting_team_id, bowling_team_id
