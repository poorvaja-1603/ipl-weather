with raw_weather as (
    select * from {{ source('raw', 'weather_hourly') }}
),

flattened as (
    select
        w.venue_id,
        parse_datetime('%Y-%m-%dT%H:%M', json_value(t)) as observed_at,
        safe_cast(json_value(json_query_array(w.temperature_2m)[safe_offset(i)]) as float64) as temperature_c,
        safe_cast(json_value(json_query_array(w.relative_humidity_2m)[safe_offset(i)]) as float64) as humidity_pct,
        safe_cast(json_value(json_query_array(w.dew_point_2m)[safe_offset(i)]) as float64) as dew_point_c,
        safe_cast(json_value(json_query_array(w.precipitation)[safe_offset(i)]) as float64) as precipitation_mm,
        safe_cast(json_value(json_query_array(w.wind_speed_10m)[safe_offset(i)]) as float64) as wind_kmh
    from raw_weather as w,
        unnest(json_query_array(w.`time`)) as t with offset as i
    where t is not null
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
where observed_at is not null
