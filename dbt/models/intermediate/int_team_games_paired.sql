with games as (

    select * from {{ ref('stg_team_games') }}

),

paired as (

    select
        g.game_id,
        g.team_id,
        g.season,
        g.game_date,
        g.team_abbreviation,
        g.is_home,
        g.is_win,
        g.pts,
        g.plus_minus,
        o.team_id                       as opponent_team_id,
        o.team_abbreviation             as opponent_abbreviation,
        o.pts                           as opponent_pts,
        g.pts - o.pts                   as point_diff,
        not (g.is_home or o.is_home)
            or (g.season = '2019-20' and g.game_date >= '2020-07-30')
                                        as is_neutral_site

    from games as g
    inner join games as o
        on  o.game_id = g.game_id
        and o.team_id <> g.team_id

)

select * from paired
