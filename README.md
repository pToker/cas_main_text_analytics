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