with matches as (
    select
        m.*,
        v.venue_name
    from {{ ref('fct_match') }} m
    left join {{ ref('dim_venue') }} v on m.venue_id = v.venue_id
)

select
    venue_id,
    venue_name,
    count(case when result_type != 'no_result' then 1 end) as matches_played,
    round(avg(first_innings_runs), 2) as avg_first_innings_runs,
    round(100.0 * safe_divide(countif(chasing_team_won), countif(result_type != 'no_result')), 2) as chase_win_pct,
    round(100.0 * safe_divide(countif(chasing_team_won is false and result_type != 'no_result'), countif(result_type != 'no_result')), 2) as bat_first_win_pct,
    round(100.0 * safe_divide(countif(toss_winner_id = winner_id and result_type != 'no_result'), countif(result_type != 'no_result')), 2) as toss_winner_match_win_pct
from matches
group by venue_id, venue_name
