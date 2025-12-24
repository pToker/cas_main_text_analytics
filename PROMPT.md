I am continuing an existing Python backend project and need your help.

Project goal:

FastAPI app that syncs personal Gmail emails into PostgreSQL

Incremental sync via Gmail historyId

Resumable after crashes

Single active sync enforced via database lock

No HTML bodies, no attachments

Labels stored with readable names

Schema changes managed ONLY via Alembic

Logging via Python stdlib, default WARNING, configurable via env

Timezone-aware UTC datetimes only

Async processing for faster email sync (concurrent Gmail API calls and DB writes)

Environment:

Python 3.12

FastAPI

SQLAlchemy (async for runtime, sync for Alembic)

Alembic

PostgreSQL

Gmail API

Constraints:

I am a beginner

Whenever you provide code:

Provide the FULL content of every file that needs to be touched

Provide the exact file path

Prefer correctness and clarity over cleverness

Prefer async for runtime, but migrations stay sync

Production-safe defaults only

Current project structure:
.
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 195926cd937f_create_initial_tables.py
│       └── f33c4b7feb88_add_performance_indexes.py
├── alembic.ini
├── app
│   ├── config.py
│   ├── credentials.json
│   ├── db.py
│   ├── gmail
│   │   ├── client.py
│   │   └── sync.py
│   ├── logging.py
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   ├── routers
│   │   └── sync.py
│   └── token.pickle
├── ENV

Relevant files for this task:

app/db.py → switched to async engine

app/models.py → DateTime(timezone=True) for all timestamps

app/gmail/sync.py → fully async, concurrency with semaphore, UTC-aware timestamps

alembic/env.py → uses sync psycopg2 URL for migrations

app/config.py → separate DATABASE_URL (asyncpg) and DATABASE_URL_ALEMBIC (psycopg2)

Goal of this change:

Enable asynchronous, concurrent syncing of Gmail messages to PostgreSQL

Avoid mixing naive and aware datetimes

Preserve full/incremental sync logic and single active lock

Keep schema migrations fully compatible with Alembic

Current behavior:

Sync is synchronous and sequential (psycopg2) → slow for large inboxes

Naive vs aware datetime issues before timezone=True columns

Async model and session now implemented but concurrency not yet optimized for batch processing

Expected behavior:

Emails processed concurrently in batches with async DB writes

Full and incremental sync fully preserved

UTC-aware timestamps only

Single active sync enforced

Migrations via Alembic still fully functional with synchronous engine

Faster sync times without breaking existing logic