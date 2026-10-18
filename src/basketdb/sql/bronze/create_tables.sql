-- Couche Bronze : données brutes de stats.nba.com, une table par grain.
-- Script idempotent : peut être exécuté autant de fois que nécessaire.

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.team_game_log (
    season      text        NOT NULL CHECK (season ~ '^[0-9]{4}-[0-9]{2}$'),
    payload     jsonb       NOT NULL,
    _loaded_at  timestamptz NOT NULL DEFAULT now(),
    _source     text        NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.player_game_log (
    season      text        NOT NULL CHECK (season ~ '^[0-9]{4}-[0-9]{2}$'),
    payload     jsonb       NOT NULL,
    _loaded_at  timestamptz NOT NULL DEFAULT now(),
    _source     text        NOT NULL
);

CREATE INDEX IF NOT EXISTS team_game_log_season_idx ON bronze.team_game_log (season);
CREATE INDEX IF NOT EXISTS player_game_log_season_idx ON bronze.player_game_log (season);

COMMENT ON TABLE bronze.team_game_log IS
    'Journal des matchs de saison régulière, brut. Grain : une ligne par équipe et par match (payload GAME_ID, TEAM_ID).';
COMMENT ON TABLE bronze.player_game_log IS
    'Journal des matchs de saison régulière, brut. Grain : une ligne par joueur et par match (payload GAME_ID, PLAYER_ID).';