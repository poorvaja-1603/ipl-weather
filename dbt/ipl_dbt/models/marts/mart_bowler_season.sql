with deliveries as (
    select
        d.*,
        m.season_year
    from {{ ref('stg_deliveries') }} d
    inner join {{ ref('stg_matches') }} m on d.match_id = m.match_id
    where not d.is_super_over_innings
)

select
    bowler,
    season_year,
    countif(is_legal_ball) as balls_bowled,
    round(safe_divide(countif(is_legal_ball), 6.0), 1) as overs,
    sum(total_runs) as runs_conceded,
    countif(is_wicket and dismissal_kind not in ('run out', 'retired hurt', 'obstructing the field')) as wickets,
    round(safe_divide(sum(total_runs) * 6.0, countif(is_legal_ball)), 2) as economy
from deliveries
group by bowler, season_year
