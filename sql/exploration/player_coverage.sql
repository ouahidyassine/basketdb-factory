-- Profilage du journal joueur : contient-il les joueurs qui n'ont pas joué ?
-- Exécution : psql -h localhost -p 5433 -U basketdb_user -d basketdb -f sql/exploration/player_coverage.sql

-- 1. Type JSON du champ MIN.
SELECT jsonb_typeof(payload->'MIN') AS type_min, count(*) AS lignes
FROM bronze.player_game_log
GROUP BY 1;

-- 2. Nombre de joueurs par équipe et par match.
SELECT min(n) AS minimum, round(avg(n), 2) AS moyenne, max(n) AS maximum
FROM (
    SELECT count(*) AS n
    FROM bronze.player_game_log
    GROUP BY payload->>'GAME_ID', payload->>'TEAM_ID'
) AS par_equipe_match;

-- 3. Lignes à 0 minute, ou sans minutes.
SELECT
    count(*) FILTER (WHERE payload->'MIN' = '0'::jsonb) AS zero_minute,
    count(*) FILTER (
        WHERE payload->'MIN' IS NULL OR jsonb_typeof(payload->'MIN') = 'null'
    ) AS sans_minutes
FROM bronze.player_game_log;

-- 4. Les lignes à 0 minute sont-elles des joueurs entrés moins d'une minute ?
SELECT
    count(*) FILTER (WHERE (payload->>'MIN')::numeric % 1 <> 0) AS minutes_non_entieres,
    count(*) FILTER (WHERE payload->'MIN' = '0'::jsonb) AS zero_minute,
    count(*) FILTER (
        WHERE payload->'MIN' = '0'::jsonb
          AND (
              (payload->>'PLUS_MINUS')::int <> 0
              OR (payload->>'FGA')::int > 0
              OR (payload->>'REB')::int > 0
              OR (payload->>'PF')::int > 0
          )
    ) AS zero_minute_avec_activite
FROM bronze.player_game_log;
