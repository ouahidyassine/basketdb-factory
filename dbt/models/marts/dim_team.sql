with ranked as (

    select
        team_id,
        team_abbreviation,
        team_name,
        row_number() over (
            partition by team_id
            order by game_date desc
        )                                          as recency_rank

    from {{ ref('stg_team_games') }}

)

select
    team_id,
    team_abbreviation,
    team_name

from ranked
where recency_rank = 1
