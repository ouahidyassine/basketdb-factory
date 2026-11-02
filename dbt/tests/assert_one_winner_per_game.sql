-- Chaque match doit avoir exactement un vainqueur.
select
    game_id,
    count(*) filter (where is_win) as vainqueurs

from {{ ref('fact_team_game') }}
group by game_id
having count(*) filter (where is_win) <> 1
