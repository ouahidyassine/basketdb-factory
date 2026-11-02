-- Chaque match doit compter exactement deux lignes : une par équipe.
select
    game_id,
    count(*) as lignes

from {{ ref('fact_team_game') }}
group by game_id
having count(*) <> 2
