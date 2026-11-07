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
    opponent_win_rate_last_10,
    case
        when is_neutral_site then 'Terrain neutre'
        when is_home then 'Domicile'
        else 'Extérieur'
    end                                          as venue,
    case when is_win then 'Victoire' else 'Défaite' end
                                                 as result,
    case
        when rest_days is null then 'Premier match'
        when rest_days = 0 then '0 jour (back-to-back)'
        when rest_days = 1 then '1 jour'
        when rest_days = 2 then '2 jours'
        else '3 jours et plus'
    end                                          as rest_bucket,
    case
        when rest_days is null then 0
        when rest_days >= 3 then 4
        else rest_days + 1
    end                                          as rest_bucket_order

from games
