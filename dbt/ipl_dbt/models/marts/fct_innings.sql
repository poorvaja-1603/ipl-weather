select
    match_id,
    innings_no,
    batting_team_id,
    bowling_team_id,
    total_runs,
    wickets,
    overs,
    run_rate,
    extras
from {{ ref('int_innings_totals') }}
