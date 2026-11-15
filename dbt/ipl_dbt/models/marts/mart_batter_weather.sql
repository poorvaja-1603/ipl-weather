with deliveries as (
    select
        d.*,
        m.humidity_band
    from {{ ref('stg_deliveries') }} d
    inner join {{ ref('fct_match') }} m on d.match_id = m.match_id
    where not d.is_super_over_innings
)

select
    batter,
    humidity_band,
    countif(is_legal_ball) as balls_faced,
    sum(batter_runs) as runs,
    round(100.0 * safe_divide(sum(batter_runs), countif(is_legal_ball)), 2) as strike_rate
from deliveries
where humidity_band is not null
group by batter, humidity_band
