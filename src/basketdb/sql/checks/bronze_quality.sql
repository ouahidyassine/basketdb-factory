-- Contrôles de qualité de la couche Bronze.
-- Chaque contrôle compte des violations : 0 partout signifie que la couche est saine.
-- Exécution : psql -h localhost -p 5433 -U basketdb_user -d basketdb -f src/basketdb/sql/checks/bronze_quality.sql

WITH team AS (
    SELECT
        payload->>'GAME_ID' AS game_id,
        payload->>'TEAM_ID' AS team_id,
        payload->>'WL' AS wl,
        (payload->>'PTS')::int AS pts
    FROM bronze.team_game_log
),
player AS (
    SELECT
        payload->>'GAME_ID' AS game_id,
        payload->>'TEAM_ID' AS team_id,
        payload->>'PLAYER_ID' AS player_id
    FROM bronze.player_game_log
)
SELECT 'équipe : doublons sur (GAME_ID, TEAM_ID)' AS controle, count(*) AS violations
FROM (SELECT game_id, team_id FROM team GROUP BY game_id, team_id HAVING count(*) > 1) AS d
UNION ALL
SELECT 'équipe : matchs sans exactement 2 lignes', count(*)
FROM (SELECT game_id FROM team GROUP BY game_id HAVING count(*) <> 2) AS d
UNION ALL
SELECT 'équipe : matchs sans exactement 1 victoire', count(*)
FROM (
    SELECT game_id FROM team
    GROUP BY game_id
    HAVING count(*) FILTER (WHERE wl = 'W') <> 1
) AS d
UNION ALL
SELECT 'équipe : vainqueur sans plus de points que le perdant', count(*)
FROM team AS w
JOIN team AS l ON l.game_id = w.game_id AND l.team_id <> w.team_id
WHERE w.wl = 'W' AND w.pts <= l.pts
UNION ALL
SELECT 'joueur : doublons sur (GAME_ID, PLAYER_ID)', count(*)
FROM (SELECT game_id, player_id FROM player GROUP BY game_id, player_id HAVING count(*) > 1) AS d
UNION ALL
SELECT 'joueur : lignes sans ligne équipe pour le même match', count(*)
FROM player AS p
WHERE NOT EXISTS (
    SELECT 1 FROM team AS t WHERE t.game_id = p.game_id AND t.team_id = p.team_id
)
UNION ALL
SELECT 'équipe : clés manquantes', count(*)
FROM team
WHERE game_id IS NULL OR team_id IS NULL OR wl IS NULL;
