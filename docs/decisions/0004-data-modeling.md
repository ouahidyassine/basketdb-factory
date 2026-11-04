# ADR 0004 — Modélisation des couches Silver et Gold avec dbt

- Statut : accepté
- Date : 2026-11-04

## Contexte

Bronze stocke chaque ligne de la source dans une colonne JSONB. Power BI a besoin d'un modèle prêt pour l'analyse, qui réponde à la question : peut-on expliquer le résultat d'un match avant qu'il soit joué ? Les transformations doivent être versionnées, testées, documentées, et rejouées chaque jour.

## Décision

- **dbt** (dbt-core 1.12, dbt-postgres 1.11), installé dans le venv du projet comme dépendance optionnelle (`pip check` sans conflit) ; `profiles.yml` versionné, qui lit la connexion par `env_var()`.
- **Trois couches** : staging en vues dans `silver` (extraction et typage, une source par modèle) ; intermediate en vues dans `silver` (logique métier) ; marts en tables dans `gold`.
- **Variables d'avant-match** : adversaire par auto-jointure, repos et back-to-back par `lag()`, forme sur les 10 matchs précédents par une fenêtre `rows between 10 preceding and 1 preceding`, qui exclut le match courant.
- **Terrain neutre** : un match sans équipe à domicile dans la source (10 matchs en 2024-25 et 2025-26), ou un match de la bulle de 2019-20, à partir du 30 juillet 2020.
- **Schéma en étoile** au grain équipe et match : `fact_team_game`, et `dim_team`, `dim_date`, `dim_season` ; clés naturelles ; `dim_team` joue deux rôles, l'équipe et l'adversaire.
- **Gold limité au niveau équipe en v1.0** ; le niveau joueur reste dans Silver, où il sert au rapprochement des points.
- **Qualité** : 54 tests génériques et 4 tests singuliers ; `dbt build` en fin de DAG, après la porte de qualité de Bronze, sans reprise ; `dbt parse` dans la CI.

## Alternatives écartées

- **Des scripts SQL lancés à la main** : ni ordre d'exécution calculé, ni tests, ni lineage.
- **Des transformations en pandas** : les données sortiraient de la base, et la logique serait moins lisible pour un analyste.
- **Gold en vues** : Power BI relirait toute la chaîne de vues à chaque requête.
- **Des clés artificielles** : aucun bénéfice, les clés naturelles sont stables et lisibles.
- **Un fait joueur dans Gold dès la v1.0** : aucune page du dashboard v1.0 ne l'utiliserait ; reporté en v1.1.
- **Une tâche Airflow par modèle dbt** : de la complexité sans gain, pour un `dbt build` de quelques secondes.
- **Un venv dédié à dbt** : inutile, aucune dépendance n'entre en conflit avec le projet.

## Conséquences

- La lignée, la documentation et les tests sont générés par dbt ; une donnée incohérente bloque le run avant d'atteindre le dashboard.
- Gold est reconstruit entièrement chaque jour, en quelques secondes : un chargement incrémental n'est pas nécessaire à ce volume.
- `is_complete` dépend de la date du jour, avec la même règle de saison qu'en Python : deux implémentations à garder cohérentes.
- `dim_date` s'arrête au 30 juin 2027 : à prolonger avant la saison 2027-28 ; le test de relation échouera sinon.
- Les matchs délocalisés antérieurs à 2024-25, hors bulle, ne sont pas détectables : la source leur attribuait une équipe à domicile.
