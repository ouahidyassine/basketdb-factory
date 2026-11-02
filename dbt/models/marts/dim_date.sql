with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-10-01' as date)",
        end_date="cast('2027-07-01' as date)"
    ) }}

),

with_season as (

    select
        date_day::date                                       as date_day,
        extract(year from date_day)::int                     as year,
        extract(month from date_day)::int                    as month,
        to_char(date_day, 'YYYY-MM')                         as year_month,
        extract(isodow from date_day)::int                   as day_of_week,
        extract(isodow from date_day) in (6, 7)              as is_weekend,
        case
            when extract(month from date_day) >= 10 then extract(year from date_day)::int
            else extract(year from date_day)::int - 1
        end                                                  as season_start_year

    from spine

)

select
    date_day,
    year,
    month,
    year_month,
    day_of_week,
    is_weekend,
    season_start_year::text || '-'
        || lpad(((season_start_year + 1) % 100)::text, 2, '0')   as season

from with_season
