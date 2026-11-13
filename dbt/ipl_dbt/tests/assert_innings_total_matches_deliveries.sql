with deliveries_sum as (
    select
        match_id,
        innings_no,
        sum(total_runs) as calc_total_runs
    from {{ ref('stg_deliveries') }}
    group by match_id, innings_no
),

innings_reported as (
    select
        match_id,
        innings_no,
        total_runs
    from {{ ref('fct_innings') }}
)

select
    d.match_id,
    d.innings_no,
    d.calc_total_runs,
    i.total_runs as reported_total_runs
from deliveries_sum d
inner join innings_reported i
    on d.match_id = i.match_id
    and d.innings_no = i.innings_no
where d.calc_total_runs != i.total_runs
