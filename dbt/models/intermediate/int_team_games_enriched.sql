with paired as (

    select * from {{ ref('int_team_games_paired') }}

),

team_history as (

    select
        *,
        row_number() over team_season                as game_number,
        lag(game_date) over team_season              as previous_game_date,
        avg(is_win::int) over (
            team_season rows between 10 preceding and 1 preceding
        )                                            as win_rate_last_10,
        count(*) over (
            team_season rows between 10 preceding and 1 preceding
        )                                            as form_games

    from paired
    window team_season as (partition by team_id, season order by game_date)

),

with_rest as (

    select
        *,
        game_date - previous_game_date - 1           as rest_days

    from team_history

),

with_opponent as (

    select
        t.*,
        t.rest_days = 0                              as is_back_to_back,
        o.rest_days                                  as opponent_rest_days,
        t.rest_days - o.rest_days                    as rest_advantage,
        o.win_rate_last_10                           as opponent_win_rate_last_10

    from with_rest as t
    inner join with_rest as o
        on  o.game_id = t.game_id
        and o.team_id = t.opponent_team_id

)

select * from with_opponent
