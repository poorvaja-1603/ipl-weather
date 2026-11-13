with team_matches as (
    select
        season_year,
        match_id,
        team1_id as team_id,
        winner_id,
        result_type,
        first_innings_runs as runs_scored,
        second_innings_runs as runs_conceded
    from {{ ref('fct_match') }}
    union all
    select
        season_year,
        match_id,
        team2_id as team_id,
        winner_id,
        result_type,
        second_innings_runs as runs_scored,
        first_innings_runs as runs_conceded
    from {{ ref('fct_match') }}
)

select
    tm.team_id,
    dt.team_name,
    tm.season_year,
    count(case when tm.result_type != 'no_result' then 1 end) as matches,
    count(case when tm.winner_id = tm.team_id then 1 end) as wins,
    round(100.0 * count(case when tm.winner_id = tm.team_id then 1 end) / nullif(count(case when tm.result_type != 'no_result' then 1 end), 0), 2) as win_pct,
    round(avg(tm.runs_scored), 2) as avg_runs_scored,
    round(avg(tm.runs_conceded), 2) as avg_runs_conceded
from team_matches tm
left join {{ ref('dim_team') }} dt on tm.team_id = dt.team_id
group by tm.team_id, dt.team_name, tm.season_year
