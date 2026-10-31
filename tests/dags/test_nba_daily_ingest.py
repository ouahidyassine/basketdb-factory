"""Tests du DAG nba_daily_ingest : import, tâches, ordre, planification et reprises."""
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from airflow.sdk import DAG

pytest.importorskip("airflow", reason="Airflow n'est pas installé dans cet environnement")

DAG_FILE = Path(__file__).resolve().parents[2] / "dags" / "nba_daily_ingest.py"
INGEST_TASKS = ("ingest_team", "ingest_player")


def load_dag_module() -> ModuleType:
    """Exécute le fichier du DAG par son chemin, comme le dag-processor, et renvoie le module."""
    spec = importlib.util.spec_from_file_location("nba_daily_ingest", DAG_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dag() -> "DAG":
    """Le DAG, chargé une seule fois pour tous les tests du fichier."""
    return load_dag_module().dag


def test_dag_has_expected_tasks(dag: "DAG") -> None:
    assert set(dag.task_ids) == {"ingest_team", "ingest_player", "check_bronze_quality"}


def test_tasks_run_in_order(dag: "DAG") -> None:
    assert dag.get_task("ingest_team").downstream_task_ids == {"ingest_player"}
    assert dag.get_task("ingest_player").downstream_task_ids == {"check_bronze_quality"}
    assert dag.get_task("check_bronze_quality").downstream_task_ids == set()


def test_schedule_is_daily_without_catchup(dag: "DAG") -> None:
    assert dag.schedule == "0 10 * * *"
    assert dag.catchup is False
    assert dag.max_active_runs == 1


def test_ingestion_loads_the_season_of_the_run_date(dag: "DAG") -> None:
    for task_id in INGEST_TASKS:
        assert "--date {{ ds }}" in dag.get_task(task_id).bash_command


def test_only_ingestion_is_retried(dag: "DAG") -> None:
    for task_id in INGEST_TASKS:
        assert dag.get_task(task_id).retries == 2
    assert dag.get_task("check_bronze_quality").retries == 0
