with raw_deliveries as (
    select * from {{ source('raw', 'ipl_deliveries') }}
),

team_mapping as (
    select * from {{ ref('team_map') }}
),

parsed as (
    select
        safe_cast(d.match_id as int64) as match_id,
        safe_cast(coalesce(d.innings, d.inning) as int64) as innings_no,
        safe_cast(coalesce(d.over_no, d.over) as int64) as over_no,
        safe_cast(coalesce(d.ball_no, d.ball) as int64) as ball_no,
        trim(cast(coalesce(d.batting_team, '') as string)) as raw_batting_team,
        trim(cast(coalesce(d.bowling_team, '') as string)) as raw_bowling_team,
        trim(cast(coalesce(d.batter, d.batsman) as string)) as batter,
        trim(cast(d.bowler as string)) as bowler,
        safe_cast(coalesce(d.batter_runs, d.batsman_runs, 0) as int64) as batter_runs,
        safe_cast(coalesce(d.extra_runs, 0) as int64) as extra_runs,
        safe_cast(coalesce(d.total_runs, 0) as int64) as total_runs,
        safe_cast(coalesce(d.wides, 0) as int64) as wides,
        safe_cast(coalesce(d.noballs, 0) as int64) as noballs,
        case
            when safe_cast(d.is_wicket as int64) = 1
              or (d.dismissal_kind is not null and trim(cast(d.dismissal_kind as string)) != '')
            then true
            else false
        end as is_wicket,
        trim(cast(d.dismissal_kind as string)) as dismissal_kind
    from raw_deliveries d
)

select
    p.match_id,
    p.innings_no,
    p.over_no,
    p.ball_no,
    coalesce(t_bat.team_id, p.raw_batting_team) as batting_team_id,
    coalesce(t_bowl.team_id, p.raw_bowling_team) as bowling_team_id,
    p.batter,
    p.bowler,
    p.batter_runs,
    p.extra_runs,
    p.total_runs,
    case when p.wides = 0 and p.noballs = 0 then true else false end as is_legal_ball,
    p.is_wicket,
    p.dismissal_kind,
    case when p.innings_no >= 3 then true else false end as is_super_over_innings
from parsed p
left join team_mapping t_bat on p.raw_batting_team = t_bat.raw_team_name
left join team_mapping t_bowl on p.raw_bowling_team = t_bowl.raw_team_name
