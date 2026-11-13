with raw_deliveries as (
    select * from {{ source('raw', 'ipl_deliveries') }}
),

team_mapping as (
    select * from {{ ref('team_map') }}
)

select
    d.match_id::int as match_id,
    d.inning::int as innings_no,
    d.over::int as over_no,
    d.ball::int as ball_no,
    coalesce(t_bat.team_id, d.batting_team) as batting_team_id,
    coalesce(t_bowl.team_id, d.bowling_team) as bowling_team_id,
    d.batsman as batter,
    d.bowler as bowler,
    d.batsman_runs::int as batter_runs,
    d.extra_runs::int as extra_runs,
    d.total_runs::int as total_runs,
    case when d.is_wicket::int = 1 or d.dismissal_kind is not null then true else false end as is_wicket,
    d.dismissal_kind
from raw_deliveries d
left join team_mapping t_bat on trim(d.batting_team) = trim(t_bat.raw_team_name)
left join team_mapping t_bowl on trim(d.bowling_team) = trim(t_bowl.raw_team_name)
