select distinct
    team_id,
    team_name,
    short_name
from {{ ref('team_map') }}
