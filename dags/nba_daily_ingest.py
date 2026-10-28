"""DAG quotidien : recharge dans Bronze la saison NBA de la date du run."""
from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT_DIR = Path(__file__).resolve().parents[1]
INGEST_BIN = PROJECT_DIR / ".venv" / "bin" / "basketdb-ingest"


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
    description="Recharge chaque jour la saison NBA en cours dans la couche Bronze.",
    schedule="0 10 * * *",
    start_date=datetime(2026, 10, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["basketdb", "bronze"],
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

    ingest_team >> ingest_player
