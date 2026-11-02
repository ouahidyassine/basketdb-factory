-- Un match a au plus une équipe à domicile ;
-- s'il n'en a aucune, il doit être marqué comme joué sur terrain neutre.
select
    game_id,
    count(*) filter (where is_home)  as equipes_a_domicile,
    bool_and(is_neutral_site)        as terrain_neutre

from {{ ref('fact_team_game') }}
group by game_id
having count(*) filter (where is_home) > 1
    or (count(*) filter (where is_home) = 0 and not bool_and(is_neutral_site))
