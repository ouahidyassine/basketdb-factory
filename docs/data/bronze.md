# Couche Bronze

Données brutes de stats.nba.com (endpoint `LeagueGameLog`), chargées par `basketdb-ingest` saison par saison, de façon idempotente. Chaque ligne de la source est stockée telle quelle dans la colonne `payload` (JSONB).

## Tables

| Table | Grain | Clé (dans `payload`) | Lignes, 2015-16 à 2025-26 |
|---|---|---|---|
| `bronze.team_game_log` | Une ligne par équipe et par match | `(GAME_ID, TEAM_ID)` | 26 418 |
| `bronze.player_game_log` | Une ligne par joueur entré en jeu, par match | `(GAME_ID, PLAYER_ID)` | 281 163 |

Colonnes communes : `season` (clé de partition, format `AAAA-AA`), `payload`, `_loaded_at` (horodatage du chargement, UTC), `_source`.

## Volumes par saison

| Saison | Lignes équipe | Matchs | Lignes joueur |
|---|---|---|---|
| 2015-16 | 2 460 | 1 230 | 26 078 |
| 2016-17 | 2 460 | 1 230 | 26 139 |
| 2017-18 | 2 460 | 1 230 | 26 107 |
| 2018-19 | 2 460 | 1 230 | 26 101 |
| 2019-20 | 2 118 | 1 059 | 22 393 |
| 2020-21 | 2 160 | 1 080 | 23 054 |
| 2021-22 | 2 460 | 1 230 | 26 039 |
| 2022-23 | 2 460 | 1 230 | 25 894 |
| 2023-24 | 2 460 | 1 230 | 26 401 |
| 2024-25 | 2 460 | 1 230 | 26 306 |
| 2025-26 | 2 460 | 1 230 | 26 651 |

2019-20 est écourtée (suspension COVID, puis bulle d'Orlando) ; 2020-21 compte 72 matchs par équipe.

## Contrôles de qualité

`sql/checks/bronze_quality.sql` : 7 contrôles, **0 violation** au 22 octobre 2026.

- Aucun doublon sur les clés des deux grains.
- Exactement 2 lignes équipe et 1 victoire par match ; le vainqueur a toujours plus de points.
- Chaque ligne joueur a sa ligne équipe pour le même match.
- Aucune clé manquante.

## Couverture du journal joueur

Profilage : `sql/exploration/player_coverage.sql`.

- `MIN` est un entier sur toutes les lignes : le temps de jeu est arrondi à la minute.
- 10,64 joueurs par équipe et par match en moyenne (de 6 à 15), pour 13 joueurs actifs sur une feuille de match.
- 1 020 lignes à 0 minute, dont 481 avec une activité mesurable (tir, rebond, faute ou `PLUS_MINUS` non nul) : des entrées de moins d'une minute.

**Conclusion** : le journal joueur contient tous les joueurs entrés en jeu, même quelques secondes, mais aucun joueur resté sur le banc ou inactif. Les absences ne sont pas dans les données : elles devront être inférées.

## Points d'attention pour Silver

- `GAME_DATE` est stocké en texte : à convertir en date.
- Domicile ou extérieur se déduit de `MATCHUP` (`vs.` = domicile, `@` = extérieur).
- L'adversaire se retrouve par auto-jointure sur `GAME_ID`.
- `VIDEO_AVAILABLE` et `FANTASY_PTS` sont inutiles à l'analyse.