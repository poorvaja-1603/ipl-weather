with raw_weather as (
    select * from {{ source('raw', 'weather_hourly') }}
),

flattened as (
    select
        w.venue_id,
        t.value::timestamp_ntz as observed_at,
        w.temperature_2m[t.index]::float as temperature_c,
        w.relative_humidity_2m[t.index]::float as humidity_pct,
        w.dew_point_2m[t.index]::float as dew_point_c,
        w.precipitation[t.index]::float as precipitation_mm,
        w.wind_speed_10m[t.index]::float as wind_kmh
    from raw_weather w,
    lateral flatten(input => w.time) t
)

select distinct
    venue_id,
    observed_at,
    temperature_c,
    humidity_pct,
    dew_point_c,
    precipitation_mm,
    wind_kmh
from flattened
