# BasketDB Factory

![CI](https://github.com/ouahidyassine/basketdb-factory/actions/workflows/ci.yml/badge.svg)

Pipeline ELT de données NBA : ingestion robuste depuis stats.nba.com, entrepôt PostgreSQL en architecture médaillon, orchestration Airflow, modélisation dbt et dashboard Power BI.

## Question analytique

**Peut-on expliquer le résultat d'un match avant qu'il soit joué ?** Avantage du terrain, jours de repos, matchs consécutifs, forme récente : le projet mesure le poids de chaque facteur sur les saisons régulières 2015-16 à 2025-26.

## Architecture

```mermaid
flowchart LR
    G[Airflow<br/>nba_daily_ingest] -->|chaque jour<br/>à 10 h UTC| B
    A[stats.nba.com<br/>via nba_api] -->|extraction avec reprises<br/>et contrat de schéma| B[basketdb-ingest]
    B -->|COPY idempotent<br/>par saison| C[(PostgreSQL<br/>bronze)]
    C -.->|dbt · phase 3| D[(silver)]
    D -.->|dbt · phase 3| E[(gold)]
    E -.->|phase 4| F[Power BI]
```

Traits pleins : construit. Pointillés : à venir. Chaque jour, le DAG `nba_daily_ingest` recharge la saison en cours aux niveaux équipe et joueur.

## Avancement

| Phase | Contenu | État |
|---|---|---|
| 0 | Environnement local, validation de la source | ✅ `v0.1.0` |
| 1 | Ingestion Bronze : 11 saisons, 307 581 lignes | ✅ `v0.2.0` |
| 2 | Orchestration Airflow | En cours |
| 3 | Modélisation dbt (Silver, Gold), tests et lineage | À venir |
| 4 | Dashboard Power BI | À venir |

## Démarrage rapide

Prérequis : Python 3.12 et PostgreSQL 16, avec le rôle et la base décrits dans [docs/setup.md](docs/setup.md).

```bash
git clone git@github.com:ouahidyassine/basketdb-factory.git
cd basketdb-factory
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # puis renseigner POSTGRES_PASSWORD
basketdb-ingest --from 2015-16 --to 2025-26
```

Le backfill complet prend environ 1 min 30. Il est idempotent : le relancer remplace chaque saison à l'identique, sans doublon.

Pour charger la saison d'une date précise, comme le fait le DAG :

```bash
basketdb-ingest --date 2026-01-15
```

## Qualité

- **65 tests** (`pytest`) : 59 tests unitaires, sans réseau ni base, et 6 tests d'intégration contre PostgreSQL, exécutés dans une transaction annulée.
- **CI GitHub Actions** : `ruff` et `pytest` sur chaque pull request ; `main` est protégée, aucune fusion n'est possible sans CI verte.
- **7 contrôles de qualité des données** sur Bronze (grain, cardinalité, cohérence métier, intégrité référentielle, complétude), exécutés par `basketdb-check` à la fin de chaque run du DAG : une violation fait échouer le run.

```bash
pytest
basketdb-check
```

## Structure du dépôt

```
basketdb-factory/
├── src/basketdb/          # package : configuration, extraction, contrat, chargement, CLI
│   └── sql/               # SQL exécuté par le code : DDL Bronze, contrôles de qualité
├── dags/                  # DAG Airflow : ingestion quotidienne
├── tests/                 # tests unitaires et d'intégration
├── sql/exploration/       # requêtes de profilage
├── docs/                  # installation, décisions d'architecture, documentation des données
├── spikes/                # test de faisabilité de la source
└── .github/workflows/     # intégration continue
```

## Documentation

- [Installation de l'environnement local](docs/setup.md)
- [Couche Bronze : tables, volumes, contrôles, couverture des données](docs/data/bronze.md)
- [ADR 0001 : choix de la source de données](docs/decisions/0001-source-nba-api.md)
- [ADR 0002 : stratégie de chargement de Bronze](docs/decisions/0002-bronze-loading-strategy.md)
