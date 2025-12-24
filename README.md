# Status

https://chatgpt.com/share/694abbb8-6814-8008-9b1d-07ed83c6ca93


# Run

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```


# DB & Models (ORM)
I am new to alembic (and the whole SQLAlchemy for that), so please point out obvious flaws here.

<!-- details open -->
<details>
<summary>alembic cheatsheet</summary>

## About

[alembic](https://alembic.sqlalchemy.org/) is the migration tool for [SQLAlchemy](https://www.sqlalchemy.org/)

## Commands

| command           | explanation                                                                           |
| ----------------- | ------------------------------------------------------------------------------------  |
| `alembic history` |  shows all commits and where the head is at (simmilar to `git history`)               |

</details>

## Initial migration

```bash
alembic init alembic
```
generates a version (/alembic/versions/...)

## Updates (How to handle future changes)

Change a model in app/models.py
Example: add a column priority = Column(Integer, default=0) to Email

Run:
```bash
alembic revision --autogenerate -m "add priority to email"
alembic upgrade head
```

Database is updated safely, no data lost.

# Scope
1. use gmail api to get all emails
    1. store the emails in a database
    1. generate embeddings
1. tf-idf + svm
1. [xnli](https://github.com/facebookresearch/XNLI) (zero shot transformer) / [xlm](https://huggingface.co/FacebookAI/xlm-roberta-large)
1. llm mit topic modelling (lektion vom 2025-12-16)?
    1. Promten, dass diese labels mit diesen stichworten relevant sind.
    1. oder nur die labels

# To Do Next
- [x] acknowledge, that I have to work locally, as raspi does not have gpu
- [ ] initiate a project, with local env to make sure I don't publish my sensitive information
- [ ] install postgresql

# Open Tasks (beyond scope of CAS_MAIN project)
- [ ] Production readiness (not just `fastapi dev app/main.py`)
- [ ] authentication

# Installation & Setup
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


### Create the database
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

### Create the tables for email and labels
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gmail_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    subject TEXT,
    sender TEXT,
    body TEXT,
    cleaned_text TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE,
    in_inbox BOOLEAN DEFAULT true,

    predicted_labels JSONB,
    applied_labels JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
-- CREATE TABLE
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);
-- CREATE TABLE
CREATE TABLE training_samples (
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    label_id INT REFERENCES labels(id) ON DELETE CASCADE,
    value BOOLEAN NOT NULL,
    source TEXT CHECK (source IN ('gmail', 'manual')),

    PRIMARY KEY (email_id, label_id)
);
-- CREATE TABLE
-- helper table to keep sync state
mail_classifier=> CREATE TABLE gmail_sync_state (
    id BOOLEAN PRIMARY KEY DEFAULT TRUE,
    last_history_id TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

INSERT INTO gmail_sync_state (id, last_history_id)
VALUES (TRUE, '0');
-- CREATE TABLE
-- INSERT 0 1
-- audit trail / sync log
mail_classifier=> CREATE TABLE gmail_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type TEXT CHECK (sync_type IN ('initial', 'incremental', 'full')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    finished_at TIMESTAMP WITH TIME ZONE,
    messages_added INT DEFAULT 0,
    labels_updated INT DEFAULT 0,
    success BOOLEAN,
    error TEXT
);
-- CREATE TABLE
```

#### Indexes
```sql
CREATE INDEX idx_emails_gmail_id ON emails(gmail_id);
CREATE INDEX idx_emails_inbox ON emails(in_inbox);
CREATE INDEX idx_training_label ON training_samples(label_id);
-- CREATE INDEX
-- CREATE INDEX
-- CREATE INDEX
CREATE INDEX idx_predicted_labels ON emails USING GIN (predicted_labels);
-- CREATE INDEX
```

#### All good?
```sql
\dt
```

## Python
### venv
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install fastapi sqlalchemy psycopg2-binary alembic python-dotenv
python -m pip freeze > requirements.txt
```

### SQLAlchemy


## Gmail Setup

Enable API:
https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=simple-calendar-367516

Create Credentials:
https://console.cloud.google.com/apis/credentials?project=simple-calendar-367516

Create OAuth client ID

# Development Environment

`fastapi dev main.py`

* App locally available at: http://127.0.0.1:8000/
* App documentation (Swagger UI) locally available at: http://127.0.0.1:8000/docs#/default/sync_gmail_sync_gmail_pos
* App documentation (redoc) locally available at: http://127.0.0.1:8000/redoc
* OpenAPI JSON Schema: : http://127.0.0.1:8000/openapi.json