select distinct
    venue_id,
    venue_name,
    city,
    country,
    latitude,
    longitude
from {{ ref('venue_map') }}
