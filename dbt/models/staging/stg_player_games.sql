with source as (

    select * from {{ source('bronze', 'player_game_log') }}

),

renamed as (

    select
        payload ->> 'GAME_ID'                        as game_id,
        (payload ->> 'PLAYER_ID')::int               as player_id,
        payload ->> 'PLAYER_NAME'                    as player_name,
        (payload ->> 'TEAM_ID')::int                 as team_id,
        payload ->> 'TEAM_ABBREVIATION'              as team_abbreviation,
        season,
        (payload ->> 'GAME_DATE')::date              as game_date,
        payload ->> 'MATCHUP'                        as matchup,
        payload ->> 'WL' = 'W'                       as is_win,
        (payload ->> 'MIN')::int                     as minutes,
        (payload ->> 'PTS')::int                     as pts,
        (payload ->> 'FGM')::int                     as fgm,
        (payload ->> 'FGA')::int                     as fga,
        (payload ->> 'FG_PCT')::numeric              as fg_pct,
        (payload ->> 'FG3M')::int                    as fg3m,
        (payload ->> 'FG3A')::int                    as fg3a,
        (payload ->> 'FG3_PCT')::numeric             as fg3_pct,
        (payload ->> 'FTM')::int                     as ftm,
        (payload ->> 'FTA')::int                     as fta,
        (payload ->> 'FT_PCT')::numeric              as ft_pct,
        (payload ->> 'OREB')::int                    as oreb,
        (payload ->> 'DREB')::int                    as dreb,
        (payload ->> 'REB')::int                     as reb,
        (payload ->> 'AST')::int                     as ast,
        (payload ->> 'STL')::int                     as stl,
        (payload ->> 'BLK')::int                     as blk,
        (payload ->> 'TOV')::int                     as tov,
        (payload ->> 'PF')::int                      as pf,
        (payload ->> 'PLUS_MINUS')::int              as plus_minus,
        _loaded_at

    from source

)

select * from renamed
