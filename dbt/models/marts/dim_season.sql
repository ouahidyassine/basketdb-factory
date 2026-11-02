with seasons as (

    select
        season,
        min(game_date)             as first_game_date,
        max(game_date)             as last_game_date,
        count(distinct game_id)    as games_played

    from {{ ref('stg_team_games') }}
    group by season

),

notes as (

    select * from {{ ref('season_notes') }}

),

current_season as (

    select
        case
            when extract(month from current_date) >= 10 then extract(year from current_date)
            else extract(year from current_date) - 1
        end::int                   as start_year

)

select
    s.season,
    left(s.season, 4)::int                         as start_year,
    s.first_game_date,
    s.last_game_date,
    s.games_played,
    coalesce(n.is_shortened, false)                as is_shortened,
    n.note,
    left(s.season, 4)::int < c.start_year
        or extract(month from current_date) between 5 and 9
                                                   as is_complete

from seasons as s
cross join current_season as c
left join notes as n
    on n.season = s.season
