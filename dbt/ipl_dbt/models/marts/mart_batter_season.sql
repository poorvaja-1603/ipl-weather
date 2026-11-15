with deliveries as (
    select
        d.*,
        m.season_year
    from {{ ref('stg_deliveries') }} d
    inner join {{ ref('stg_matches') }} m on d.match_id = m.match_id
    where not d.is_super_over_innings
)

select
    batter,
    season_year,
    count(distinct match_id) as matches,
    sum(batter_runs) as runs,
    countif(is_legal_ball) as balls_faced,
    round(100.0 * safe_divide(sum(batter_runs), countif(is_legal_ball)), 2) as strike_rate,
    count(case when batter_runs = 4 then 1 end) as fours,
    count(case when batter_runs = 6 then 1 end) as sixes,
    count(case when is_wicket = true and dismissal_kind not in ('run out', 'retired hurt') then 1 end) as dismissals
from deliveries
group by batter, season_year
