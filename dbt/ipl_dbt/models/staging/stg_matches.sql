with raw_matches as (
    select * from {{ source('raw', 'ipl_matches') }}
),

venue_mapping as (
    select * from {{ ref('venue_map') }}
),

team_mapping as (
    select * from {{ ref('team_map') }}
),

parsed as (
    select
        safe_cast(m.match_id as int64) as match_id,
        coalesce(
            safe.parse_date('%Y-%m-%d', cast(m.match_date as string)),
            safe.parse_date('%d-%m-%Y', cast(m.match_date as string))
        ) as match_date,
        trim(cast(m.venue as string)) as raw_venue,
        trim(cast(m.team1 as string)) as raw_team1,
        trim(cast(m.team2 as string)) as raw_team2,
        trim(cast(m.toss_winner as string)) as raw_toss_winner,
        lower(trim(cast(m.toss_decision as string))) as toss_decision,
        trim(cast(m.winner as string)) as raw_winner,
        trim(cast(m.eliminator as string)) as raw_eliminator,
        safe_cast(m.winner_runs as int64) as winner_runs,
        safe_cast(m.winner_wickets as int64) as winner_wickets,
        lower(trim(cast(m.outcome as string))) as outcome,
        trim(cast(m.method as string)) as raw_method,
        trim(cast(m.player_of_match as string)) as player_of_match
    from raw_matches m
)

select
    p.match_id,
    extract(year from p.match_date) as season_year,
    p.match_date,
    coalesce(vm.venue_id, 'unknown') as venue_id,
    coalesce(t1.team_id, p.raw_team1) as team1_id,
    coalesce(t2.team_id, p.raw_team2) as team2_id,
    coalesce(tw.team_id, p.raw_toss_winner) as toss_winner_id,
    p.toss_decision,
    coalesce(welim.team_id, w.team_id, p.raw_winner) as winner_id,
    case
        when p.winner_runs is not null and p.winner_runs > 0 then 'runs'
        when p.winner_wickets is not null and p.winner_wickets > 0 then 'wickets'
        when p.outcome = 'tie' or (p.raw_eliminator is not null and p.raw_eliminator != '') then 'tie'
        when p.outcome in ('no result', 'abandoned') then 'no_result'
        when p.raw_winner is not null and p.raw_winner != '' then 'winner'
        else 'no_result'
    end as result_type,
    coalesce(p.winner_runs, p.winner_wickets, 0) as result_margin,
    p.player_of_match,
    case when lower(coalesce(p.raw_method, '')) in ('d/l', 'dl') then true else false end as dl_applied,
    case when p.raw_eliminator is not null and p.raw_eliminator != '' then true else false end as is_super_over
from parsed p
left join venue_mapping vm on p.raw_venue = vm.raw_venue_name
left join team_mapping t1 on p.raw_team1 = t1.raw_team_name
left join team_mapping t2 on p.raw_team2 = t2.raw_team_name
left join team_mapping tw on p.raw_toss_winner = tw.raw_team_name
left join team_mapping w on p.raw_winner = w.raw_team_name
left join team_mapping welim on p.raw_eliminator = welim.raw_team_name
