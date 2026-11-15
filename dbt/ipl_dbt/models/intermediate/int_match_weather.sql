with matches as (
    select
        match_id,
        match_date,
        venue_id
    from {{ ref('stg_matches') }}
),

weather as (
    select * from {{ ref('stg_weather_hourly') }}
),

match_weather_window as (
    select
        m.match_id,
        w.temperature_c,
        w.humidity_pct,
        w.dew_point_c,
        w.precipitation_mm,
        w.wind_kmh
    from matches m
    inner join weather w
        on m.venue_id = w.venue_id
        and w.observed_at >= datetime(m.match_date, time(19, 0, 0))
        and w.observed_at < datetime_add(datetime(m.match_date, time(19, 0, 0)), interval 3 hour)
)

select
    match_id,
    round(avg(temperature_c), 2) as avg_temp_c,
    round(avg(humidity_pct), 2) as avg_humidity_pct,
    round(avg(dew_point_c), 2) as avg_dew_point_c,
    round(sum(precipitation_mm), 2) as total_precip_mm,
    round(avg(wind_kmh), 2) as avg_wind_kmh,
    round(avg(temperature_c) - avg(dew_point_c), 2) as dew_spread_c
from match_weather_window
group by match_id
