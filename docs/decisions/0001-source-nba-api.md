# ADR 0001 — Source de données : stats.nba.com via nba_api

- Statut : accepté
- Date : 2026-09-29

## Contexte

Le projet a besoin des résultats et statistiques de tous les matchs NBA de saison régulière, de 2015-16 à la saison en cours, aux niveaux équipe et joueur. stats.nba.com est la source la plus complète, mais elle n'est ni documentée ni garantie : elle peut changer ou bloquer sans préavis.

## Décision

Utiliser la bibliothèque `nba_api` et l'endpoint `LeagueGameLog`, qui renvoie une saison complète en un seul appel, au niveau équipe (`T`) et au niveau joueur (`P`).

## Alternative écartée

- Endpoints par match (box scores) : environ 1 230 appels par saison au lieu de 2, d'où un risque de blocage élevé et un backfill beaucoup plus long.

## Résultats du test de faisabilité (`spikes/nba_api_source.py`)

| Saison | Niveau | Lignes | Matchs | Période | Durée |
|---|---|---|---|---|---|
| 2015-16 | T | 2 460 | 1 230 | 2015-10-27 → 2016-04-13 | 7,9 s |
| 2015-16 | P | 26 078 | 1 230 | 2015-10-27 → 2016-04-13 | 3,8 s |
| 2019-20 | T | 2 118 | 1 059 | 2019-10-22 → 2020-08-14 | 0,7 s |
| 2019-20 | P | 22 393 | 1 059 | 2019-10-22 → 2020-08-14 | 3,9 s |
| 2024-25 | T | 2 460 | 1 230 | 2024-10-22 → 2025-04-13 | 0,6 s |
| 2024-25 | P | 26 306 | 1 230 | 2024-10-22 → 2025-04-13 | 4,0 s |

- Grain vérifié : `(GAME_ID, TEAM_ID)` unique avec exactement 2 lignes par match ; `(GAME_ID, PLAYER_ID)` unique.
- Aucun blocage sur 6 appels espacés de 2 s.
- Versions testées : Python 3.12, nba_api  1.11.4, pandas 3.0.6, requests 2.34.2.

## Conséquences

- Domicile/extérieur à dériver de `MATCHUP` (`vs.` = domicile, `@` = extérieur) ; adversaire retrouvé par auto-jointure sur `GAME_ID`.
- Le niveau joueur semble ne contenir que les joueurs ayant joué (environ 10,6 par équipe et par match) : les absences devront être inférées. À confirmer en phase 1.
- Le nombre de matchs varie selon la saison (1 059 en 2019-20) : aucun volume codé en dur dans les contrôles qualité.
- Une saison non commencée devrait renvoyer 0 ligne (non testé) : l'ingestion quotidienne traitera ce cas comme normal.
- `GAME_DATE` arrive en texte : typage en date dans la couche Silver.
- Source non garantie, donc :
  - la couche Bronze conserve les données brutes, pour retraiter sans rappeler l'API ;
  - appels espacés, avec timeout et reprises automatiques ;
  - contrat de colonnes pour détecter tout changement de schéma.