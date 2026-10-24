# ADR 0002 — Stratégie de chargement de la couche Bronze

- Statut : accepté
- Date : 2026-10-24

## Contexte

La source renvoie une saison complète par appel. Le pipeline doit supporter le backfill de l'historique, le rechargement quotidien de la saison en cours (phase 2) et les relances après incident, sans jamais dupliquer ni perdre de données. La source n'est pas garantie : elle peut corriger des statistiques après coup, ou répondre vide lors d'un incident.

## Décision

- Une table par grain (`team_game_log`, `player_game_log`) ; chaque ligne de la source est stockée telle quelle dans une colonne `payload` en JSONB, avec `season`, `_loaded_at` et `_source`.
- La saison est la partition logique. Un chargement remplace une saison entière, en une seule transaction : suppression de la saison, `COPY` des lignes, comptage de réconciliation.
- Une extraction vide ne modifie rien.
- Le chargement quotidien rechargera la saison en cours en entier, au lieu du chargement incrémental par watermark sur `GAME_DATE` prévu au cadrage.

## Alternatives écartées

- **Colonnes typées dans Bronze** : un changement de schéma de la source casserait le chargement, et le DDL serait lourd à maintenir.
- **Ajout simple (`INSERT`)** : chaque relance crée des doublons.
- **Vidage de la table (`TRUNCATE`)** : recharger une saison effacerait toutes les autres.
- **Upsert (`ON CONFLICT`)** : il exige une clé unique extraite du JSON, et les lignes retirées de la source resteraient en base.
- **Watermark sur `GAME_DATE`** : plus complexe, et il ignore les corrections tardives de matchs déjà chargés ; inutile pour un volume de 2 appels par jour.

## Conséquences

- Chargement idempotent et atomique : relancer, c'est réparer. Grâce au MVCC de PostgreSQL, les lecteurs voient l'ancienne saison complète jusqu'au `COMMIT`, jamais une saison vide.
- Les corrections de la source sont reprises au rechargement suivant.
- Silver doit extraire et typer les champs du JSON.
- `CREATE ... IF NOT EXISTS` ne fait pas évoluer une table existante : une évolution du schéma Bronze passerait par un script de migration.
- Validation : 4 tests d'intégration (idempotence, garde, aller-retour du payload, atomicité), backfill de 11 saisons (307 581 lignes, réconciliées avec la base), 7 contrôles de qualité sans violation.