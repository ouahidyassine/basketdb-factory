"""DAG quotidien : recharge Bronze, contrôle sa qualité, puis construit Silver et Gold avec dbt."""
from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT_DIR = Path(__file__).resolve().parents[1]
INGEST_BIN = PROJECT_DIR / ".venv" / "bin" / "basketdb-ingest"
CHECK_BIN = PROJECT_DIR / ".venv" / "bin" / "basketdb-check"
DBT_BIN = PROJECT_DIR / ".venv" / "bin" / "dbt"
DBT_BUILD_COMMAND = (
    f"set -a && . ./.env && set +a && "
    f"{DBT_BIN} build --project-dir dbt --profiles-dir dbt"
)


def ingest_command(level: str) -> str:
    """Commande d'une tâche : la saison de la date logique du run, pour un niveau.

    « {{ ds }} » est un modèle Jinja, remplacé par Airflow au moment de l'exécution.
    """
    return str(INGEST_BIN) + " --date {{ ds }} --levels " + level


default_args = {
    "owner": "basketdb",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="nba_daily_ingest",
    description="Recharge la saison NBA en cours, contrôle Bronze, puis construit Silver et Gold.",
    schedule="0 10 * * *",
    start_date=datetime(2026, 10, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["basketdb", "bronze", "dbt"],
) as dag:
    ingest_team = BashOperator(
        task_id="ingest_team",
        bash_command=ingest_command("team"),
        cwd=str(PROJECT_DIR),
    )
    ingest_player = BashOperator(
        task_id="ingest_player",
        bash_command=ingest_command("player"),
        cwd=str(PROJECT_DIR),
    )
    check_bronze_quality = BashOperator(
        task_id="check_bronze_quality",
        bash_command=str(CHECK_BIN),
        cwd=str(PROJECT_DIR),
        retries=0,
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=DBT_BUILD_COMMAND,
        cwd=str(PROJECT_DIR),
        retries=0,
    )

    ingest_team >> ingest_player >> check_bronze_quality >> dbt_build
