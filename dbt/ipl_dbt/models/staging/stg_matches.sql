with raw_matches as (
    select * from {{ source('raw', 'ipl_matches') }}
),

venue_mapping as (
    select * from {{ ref('venue_map') }}
),

team_mapping as (
    select * from {{ ref('team_map') }}
)

select
    m.id::int as match_id,
    extract(year from try_to_date(m.date)) as season_year,
    try_to_date(m.date) as match_date,
    coalesce(vm.venue_id, 'unknown') as venue_id,
    coalesce(t1.team_id, m.team1) as team1_id,
    coalesce(t2.team_id, m.team2) as team2_id,
    coalesce(tw.team_id, m.toss_winner) as toss_winner_id,
    lower(m.toss_decision) as toss_decision,
    coalesce(w.team_id, m.winner) as winner_id,
    case
        when lower(m.result) = 'runs' then 'runs'
        when lower(m.result) = 'wickets' then 'wickets'
        when lower(m.result) = 'tie' then 'tie'
        else 'no_result'
    end as result_type,
    m.result_margin::int as result_margin,
    m.player_of_match,
    case when coalesce(m.method, '') = 'D/L' then true else false end as dl_applied,
    case when lower(coalesce(m.super_over, 'N')) = 'y' then true else false end as is_super_over
from raw_matches m
left join venue_mapping vm on trim(m.venue) = trim(vm.raw_venue_name)
left join team_mapping t1 on trim(m.team1) = trim(t1.raw_team_name)
left join team_mapping t2 on trim(m.team2) = trim(t2.raw_team_name)
left join team_mapping tw on trim(m.toss_winner) = trim(tw.raw_team_name)
left join team_mapping w on trim(m.winner) = trim(w.raw_team_name)
