# Installation locale

Guide d'installation de l'environnement de développement de BasketDB Factory sous Windows et WSL2.

## Prérequis

- Windows avec WSL2 et Ubuntu 24.04 LTS
- Python 3.12, fourni par Ubuntu 24.04
- Git configuré dans WSL2, avec une clé SSH enregistrée sur GitHub
- Le dépôt cloné dans le système de fichiers Linux (`~/projects/basketdb-factory`), jamais dans `/mnt/c/`, où les accès disque sont lents et les permissions Linux mal gérées

## Ports du projet

| Service | Port | Raison |
|---|---|---|
| PostgreSQL (WSL2) | 5433 | 5432 occupé par le PostgreSQL Windows de HCP |
| Airflow api-server | 8081 | 8080 occupé par un composant EDB côté Windows |

## PostgreSQL

```bash
# Rafraîchit la liste des paquets, puis installe le serveur PostgreSQL 16 et le client psql.
sudo apt update && sudo apt install -y postgresql

# Démarre le service immédiatement et à chaque ouverture de WSL.
sudo systemctl enable --now postgresql

# Passe l'instance sur le port 5433 pour éviter le conflit avec le PostgreSQL Windows.
sudo sed -i "s/^port = 5432/port = 5433/" /etc/postgresql/16/main/postgresql.conf

# Redémarre l'instance pour appliquer le nouveau port.
sudo systemctl restart postgresql

# Crée le rôle de l'entrepôt ; le mot de passe est saisi de façon interactive, donc absent de l'historique du shell.
sudo -u postgres createuser -p 5433 --pwprompt basketdb_user

# Crée la base de l'entrepôt, possédée par son rôle dédié.
sudo -u postgres createdb -p 5433 --owner=basketdb_user basketdb

# Crée le rôle d'Airflow, distinct de celui de l'entrepôt (principe du moindre privilège).
sudo -u postgres createuser -p 5433 --pwprompt airflow_user

# Crée la base de métadonnées d'Airflow, possédée par son rôle dédié.
sudo -u postgres createdb -p 5433 --owner=airflow_user airflow_db
```

## Airflow

```bash
# Installe le module venv, livré séparément sur Ubuntu.
sudo apt install -y python3-venv

# Crée un environnement virtuel dédié à Airflow, hors du dépôt, pour isoler ses dépendances.
python3 -m venv ~/venvs/airflow

# Active cet environnement dans le terminal courant.
source ~/venvs/airflow/bin/activate

# Met à jour pip dans l'environnement actif.
pip install --upgrade pip

# Fixe la version d'Airflow du projet pour que l'installation soit reproductible.
AIRFLOW_VERSION="3.3.2"

# Récupère la version courte de Python (3.12).
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

# Construit l'URL du fichier de contraintes officiel pour cette version d'Airflow et de Python.
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Installe Airflow et son provider PostgreSQL avec les versions de dépendances testées par l'équipe Airflow.
pip install "apache-airflow[postgres]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Crée le dossier de configuration d'Airflow et le dossier des DAGs du dépôt.
mkdir -p ~/airflow ~/projects/basketdb-factory/dags
```

Créer le fichier `~/airflow/airflow.env`, hors du dépôt, avec ce contenu (remplacer `TON_MOT_DE_PASSE`) :

```bash
# Dossier de travail d'Airflow (configuration, logs).
export AIRFLOW_HOME="$HOME/airflow"
# Exécute plusieurs tâches en parallèle sur la machine locale.
export AIRFLOW__CORE__EXECUTOR="LocalExecutor"
# Désactive les DAGs d'exemple fournis avec Airflow.
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
# Airflow lit les DAGs directement dans le dépôt versionné.
export AIRFLOW__CORE__DAGS_FOLDER="$HOME/projects/basketdb-factory/dags"
# Base de métadonnées d'Airflow dans PostgreSQL.
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow_user:TON_MOT_DE_PASSE@localhost:5433/airflow_db"
# Port d'écoute de l'api-server (interface et API).
export AIRFLOW__API__PORT="8081"
# Adresse à laquelle les tâches joignent l'api-server.
export AIRFLOW__API__BASE_URL="http://localhost:8081"
```

```bash
# Restreint la lecture du fichier au seul utilisateur, car il contient un mot de passe.
chmod 600 ~/airflow/airflow.env

# Charge automatiquement la configuration à chaque ouverture de terminal.
echo 'source ~/airflow/airflow.env' >> ~/.bashrc

# Recharge la configuration dans le terminal courant.
source ~/.bashrc

# Teste la connexion à la base de métadonnées.
airflow db check

# Crée ou met à niveau les tables de métadonnées d'Airflow.
airflow db migrate

# Lance l'api-server, le scheduler, le dag-processor et le triggerer en un seul processus (développement uniquement).
airflow standalone
```

Interface : `http://localhost:8081`, utilisateur `admin`, mot de passe dans `~/airflow/simple_auth_manager_passwords.json.generated`.

## Vérifications

```bash
# Vérifie que l'instance PostgreSQL 16 tourne sur le port 5433 (attendu : 16 main 5433 online).
pg_lsclusters

# Vérifie la connexion TCP avec mot de passe du rôle de l'entrepôt.
psql -h localhost -p 5433 -U basketdb_user -d basketdb -c "SELECT current_user, current_database();"

# Vérifie la connexion TCP avec mot de passe du rôle d'Airflow.
psql -h localhost -p 5433 -U airflow_user -d airflow_db -c "SELECT current_user, current_database();"

# Vérifie que les variables d'environnement l'emportent sur airflow.cfg (attendu : LocalExecutor).
airflow config get-value core executor

# Vérifie que la clé Fernet de chiffrement des Connections est définie, sans l'afficher (attendu : 45).
airflow config get-value core fernet_key | wc -c

# Vérifie que l'api-server écoute sur le port 8081 sous l'utilisateur courant.
ss -ltnp | grep ':8081 '

# Vérifie l'état de chaque composant d'Airflow (attendu : tous healthy).
curl -s http://localhost:8081/api/v2/monitor/health
```

## Dépannage

| Symptôme | Diagnostic | Cause |
|---|---|---|
| Le navigateur affiche une autre application sur un port | `netstat -ano \| findstr :PORT` (PowerShell) | Un programme Windows occupe déjà ce port |
| `ss` montre le port sans nom de processus | `sudo ss -ltnp \| grep ':PORT '` | Un processus d'un autre utilisateur (par exemple `docker-proxy`) occupe ce port |
| `Unit file postgresql.service does not exist` | `dpkg -l postgresql` | PostgreSQL n'est pas installé |
