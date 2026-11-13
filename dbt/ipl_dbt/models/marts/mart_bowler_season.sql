with deliveries as (
    select
        d.*,
        m.season_year
    from {{ ref('stg_deliveries') }} d
    inner join {{ ref('stg_matches') }} m on d.match_id = m.match_id
)

select
    bowler,
    season_year,
    count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) as balls_bowled,
    round(count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) / 6.0, 1) as overs,
    sum(total_runs) as runs_conceded,
    count(case when is_wicket = true and dismissal_kind not in ('run out', 'retired hurt', 'obstructing the field') then 1 end) as wickets,
    round(sum(total_runs) * 6.0 / nullif(count(case when extra_runs = 0 or dismissal_kind is not null then 1 end), 0), 2) as economy
from deliveries
group by bowler, season_year
