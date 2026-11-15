with raw_teams as (
    select team1 as raw_team_name from {{ source('raw', 'ipl_matches') }}
    union distinct
    select team2 from {{ source('raw', 'ipl_matches') }}
    union distinct
    select toss_winner from {{ source('raw', 'ipl_matches') }}
    union distinct
    select winner from {{ source('raw', 'ipl_matches') }}
    union distinct
    select eliminator from {{ source('raw', 'ipl_matches') }}
    union distinct
    select batting_team from {{ source('raw', 'ipl_deliveries') }}
    union distinct
    select bowling_team from {{ source('raw', 'ipl_deliveries') }}
),

clean_teams as (
    select distinct trim(cast(raw_team_name as string)) as raw_team_name
    from raw_teams
    where raw_team_name is not null and trim(cast(raw_team_name as string)) != ''
)

select clean_teams.raw_team_name
from clean_teams
left join {{ ref('team_map') }} as team_map
    on clean_teams.raw_team_name = team_map.raw_team_name
where team_map.raw_team_name is null
