# ADR 0003 — Orchestration de l'ingestion avec Airflow

- Statut : accepté
- Date : 2026-10-31

## Contexte

Airflow vit dans son propre venv, avec les versions de dépendances imposées par son fichier de contraintes ; le projet a les siennes (pandas 3, psycopg 3). Le pipeline doit recharger chaque jour la saison en cours, rester relançable à tout moment, et signaler une donnée incohérente le jour même.

## Décision

- Le DAG lance la commande `basketdb-ingest`, installée dans le venv du projet, avec un `BashOperator` : chemin absolu de la commande, dossier de travail à la racine du projet pour trouver `.env`. Le DAG n'importe jamais `basketdb`.
- La saison est déduite de la date logique du run (`--date {{ ds }}`) par `season_for_date`, une fonction testée ; jamais de la date du jour.
- Deux tâches séquentielles, `ingest_team` puis `ingest_player`, avec 2 reprises à 10 minutes ; puis `check_bronze_quality` (`basketdb-check`), sans reprise, qui fait échouer le run au moindre contrôle non nul.
- Planification quotidienne à 10 h UTC, `catchup` désactivé, un seul run actif à la fois.
- Le DAG est testé (import et structure) dans un job de CI dédié, qui installe Airflow avec ses contraintes, sans le projet.

## Alternatives écartées

- **Installer `basketdb` dans le venv d'Airflow** : conflits de dépendances entre les deux environnements.
- **`@task.external_python`** : isolation équivalente, mais la logique migrerait dans des fonctions autonomes du DAG, hors de la commande déjà testée ; le code retour d'une commande est un contrat plus simple.
- **Calculer la saison dans un modèle Jinja** : une règle métier sans test.
- **Une seule tâche pour les deux niveaux** : reprises et diagnostic moins fins.
- **Contrôler la qualité avec `psql`** : il renvoie 0 quel que soit le nombre de violations.

## Conséquences

- Isolation totale entre les deux environnements ; la commande lancée par Airflow est celle qu'un humain lance à la main, et un incident se reproduit en une ligne.
- Relancer une tâche est sans danger, grâce au chargement idempotent.
- Une donnée incohérente fait échouer le run le jour même ; un DAG cassé ne peut pas atteindre `main`.
- Le DAG suppose qu'Airflow et le projet sont sur la même machine (`LocalExecutor`) ; un déploiement distribué demanderait une image contenant le projet.
- Le DAG ne tourne que si Airflow tourne ; à son redémarrage, seul le dernier créneau manqué est rattrapé.
- Observé sous Airflow 3.3.2 : `{{ ds }}` vaut la date du créneau planifié ; pour un run manuel, l'instant du déclenchement.
