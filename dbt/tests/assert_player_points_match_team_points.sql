-- Pour chaque équipe et chaque match, la somme des points des joueurs
-- doit égaler les points de l'équipe.
with player_points as (

    select game_id, team_id, sum(pts) as player_pts
    from {{ ref('stg_player_games') }}
    group by game_id, team_id

),

team_points as (

    select game_id, team_id, pts as team_pts
    from {{ ref('stg_team_games') }}

)

select
    coalesce(t.game_id, p.game_id)   as game_id,
    coalesce(t.team_id, p.team_id)   as team_id,
    t.team_pts,
    p.player_pts

from team_points as t
full outer join player_points as p
    on  p.game_id = t.game_id
    and p.team_id = t.team_id
where t.team_pts is distinct from p.player_pts
