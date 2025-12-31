# Status

https://chatgpt.com/share/694bfb93-ae9c-8008-a820-09777285d141

<details>
    <summary>Intent</summary>

    Project goal:
    - Gmail → Postgres sync via FastAPI
    - Incremental, resumable, single-run enforced
    - Alembic migrations only
    - Logging via stdlib, default WARNING

    Python version:
    - 3.12

    Tech stack:
    - FastAPI
    - SQLAlchemy
    - Alembic
    - psycopg2
    - Gmail API

    Graciously sponsored by GPT5

</details>

<details>
    <summary>GPT Question (customer) template</summary>
    See PROMPT.md and PROJECT_STATE.md for further details.
    
    Goal of this change:
    - (one sentence)

    Current behavior:
    - (what happens now)

    Expected behavior:
    - (what should happen)

    Constraints:
    - beginner-friendly
    - full file contents
    - alembic only
    - production-safe defaults

    Relevant files:
    - app/gmail/sync.py
    - app/models.py

</details>



# Scope
- [x] use gmail api to get all emails
  - [x] store the emails in a database
  - [ ] generate embeddings
- [ ] tf-idf + svm
- [ ] [xnli](https://github.com/facebookresearch/XNLI) (zero shot transformer) / [xlm](https://huggingface.co/FacebookAI/xlm-roberta-large)
- [ ] llm mit topic modelling (lektion vom 2025-12-16)?
  - [ ] Promten, dass diese labels mit diesen stichworten relevant sind.
  - [ ] oder nur die labels

# To Do Next
- [x] acknowledge, that I have to work locally, as raspi does not have gpu
- [x] initiate a project, with local env to make sure I don't publish my sensitive information
- [x] install postgresql

# Open Tasks (beyond scope of CAS_MAIN project)
- [x] Production readiness (not just `fastapi dev app/main.py`)
- [-] authentication


# Installation & Setup

## Python
### venv
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt
pip freeze > requirements.txt
```

## PostgreSQL
### Installation
```bash
sudo apt update && sudo apt install postgresql postgresql-contrib --fix-missing

(base) tobias@thePC:~$ psql --version && systemctl is-enabled postgresql && systemctl is-active postgresql
# psql (PostgreSQL) 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
# enabled
# active
```

### Configure the RDBMS (create user & allow it to create a db)
```bash
sudo -u postgres psql
```
In the `postgres=#` prompt:
```sql
postgres=# CREATE USER mailapp WITH PASSWORD 'MY_SUPERSTRONG_PW';
-- CREATE ROLE
ALTER USER mailapp CREATEDB;
-- ALTER ROLE
```


### Create the database (obsolete due to the use of alembic?)
```sql
CREATE DATABASE mail_classifier
  WITH OWNER = mailapp
       ENCODING = 'UTF8'
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       TEMPLATE = template0;
-- CREATE DATABASE
GRANT ALL PRIVILEGES ON DATABASE mail_classifier TO mailapp;
-- GRANT
ALTER DATABASE mail_classifier SET timezone TO 'UTC';
-- ALTER DATABASE
\q
-- BYE
```
Check, whether user can login
```bash
psql -U mailapp -d mail_classifier -h localhost
```

#### HBA alteration needed for access
`sudo code /etc/postgresql/16/main/pg_hba.conf --no-sandbox --user-data-dir .`  
add lines:
```ini
local   mail_classifier   mailapp   md5
host    mail_classifier   mailapp   127.0.0.1/32   md5
```
reload the service in order to add the configuration based on the newly added lines
```bash
sudo systemctl reload postgresql
```

#### Create / enable uuid-ossp extension for UUID generation
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION
```


### SQLAlchemy ORM (Object Relational Mapper) incl. alembic
Not much of a setup done so far. Installed some python packages...


## Gmail Setup

* Enable GMail API:  [Google Cloud Console](https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=simple-calendar-367516)
* Create Credentials:  [Google Cloud Console](https://console.cloud.google.com/apis/credentials?project=simple-calendar-367516)
* Create OAuth client ID:   [Google Cloud Console](https://console.cloud.google.com/auth/clients/95314945057-snqjval7p1rdlse3bqrt1ep9pkih7f3a.apps.googleusercontent.com?project=simple-calendar-367516)
* Allow test-user to use the dev environment (e.g. my personal email address):  [Google Cloud Console](https://console.cloud.google.com/auth/audience?project=simple-calendar-367516)

### Cron Job for running the sync hourly
`crontab -l`

```ini
0 * * * * curl -X POST http://localhost:8000/sync
```

# Development Environment

`fastapi dev main.py`

* App locally available at: http://127.0.0.1:8000/
* App documentation (Swagger UI) locally available at: http://127.0.0.1:8000/docs#/default/sync_gmail_sync_gmail_pos
* App documentation (redoc) locally available at: http://127.0.0.1:8000/redoc
* OpenAPI JSON Schema: : http://127.0.0.1:8000/openapi.json

# Components
### DB & Models (ORM)
I am new to alembic (and the whole SQLAlchemy for that), so please point out obvious flaws here.

<!-- details open -->
<details>
<summary>alembic cheatsheet</summary>

#### About

[alembic](https://alembic.sqlalchemy.org/) is the migration tool for [SQLAlchemy](https://www.sqlalchemy.org/)

#### Commands

| command           | explanation                                                                           |
| ----------------- | ------------------------------------------------------------------------------------  |
| `alembic history` |  shows all commits and where the head is at (simmilar to `git history`)               |

</details>

#### Initial migration

```bash
alembic init alembic
```
generates a version (/alembic/versions/...)

#### Updates (How to handle future changes)
When adding new tables or columns, generate migrations via Alembic.

Change a model in app/models.py  
Example: add a column priority = Column(Integer, default=0) to Email

Run:
```bash
alembic revision --autogenerate -m "add priority to email"
alembic upgrade head
```



# Run

```bash
source venv/bin/activate
python main.py
```
</summary>