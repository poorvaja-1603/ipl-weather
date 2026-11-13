with deliveries as (
    select
        d.*,
        m.humidity_band
    from {{ ref('stg_deliveries') }} d
    inner join {{ ref('fct_match') }} m on d.match_id = m.match_id
)

select
    batter,
    humidity_band,
    count(case when extra_runs = 0 or dismissal_kind is not null then 1 end) as balls_faced,
    sum(batter_runs) as runs,
    round(100.0 * sum(batter_runs) / nullif(count(case when extra_runs = 0 or dismissal_kind is not null then 1 end), 0), 2) as strike_rate
from deliveries
where humidity_band is not null
group by batter, humidity_band
