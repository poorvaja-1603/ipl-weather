with raw_venues as (
    select distinct trim(cast(venue as string)) as raw_venue_name
    from {{ source('raw', 'ipl_matches') }}
    where venue is not null and trim(cast(venue as string)) != ''
)

select raw_venues.raw_venue_name
from raw_venues
left join {{ ref('venue_map') }} as venue_map
    on raw_venues.raw_venue_name = venue_map.raw_venue_name
where venue_map.raw_venue_name is null
