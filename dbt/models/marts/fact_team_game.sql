with games as (

    select * from {{ ref('int_team_games_enriched') }}

)

select
    game_id,
    team_id,
    opponent_team_id,
    game_date,
    season,
    game_number,
    is_home,
    is_neutral_site,
    is_win,
    pts,
    opponent_pts,
    point_diff,
    rest_days,
    opponent_rest_days,
    rest_advantage,
    is_back_to_back,
    form_games,
    win_rate_last_10,
    opponent_win_rate_last_10

from games
