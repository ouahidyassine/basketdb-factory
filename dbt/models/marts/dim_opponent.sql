select
    team_id              as opponent_team_id,
    team_abbreviation    as opponent_abbreviation,
    team_name            as opponent_name

from {{ ref('dim_team') }}
