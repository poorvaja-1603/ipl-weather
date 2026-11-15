with raw_weather as (
    select * from {{ source('raw', 'weather_hourly') }}
)

select distinct
    cast(venue_id as string) as venue_id,
    coalesce(
        safe.parse_datetime('%Y-%m-%dT%H:%M', cast(observed_at as string)),
        safe_cast(observed_at as datetime)
    ) as observed_at,
    safe_cast(temperature_c as float64) as temperature_c,
    safe_cast(humidity_pct as float64) as humidity_pct,
    safe_cast(dew_point_c as float64) as dew_point_c,
    safe_cast(precipitation_mm as float64) as precipitation_mm,
    safe_cast(wind_kmh as float64) as wind_kmh
from raw_weather
where observed_at is not null
