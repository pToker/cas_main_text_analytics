I am continuing an existing Python backend project and need your help.

Project goal:
- FastAPI app that syncs personal Gmail emails into PostgreSQL
- Incremental sync via Gmail historyId
- Resumable after crashes
- Single active sync enforced via database lock
- No HTML bodies, no attachments
- Labels stored with readable names
- Schema changes managed ONLY via Alembic
- Logging via Python stdlib, default WARNING, configurable via env
- Timezone-aware UTC datetimes only

Environment:
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Gmail API

Constraints:
- I am a beginner
- Whenever you provide code:
  - Provide the FULL content of every file that needs to be touched
  - Provide the exact file path
- Prefer correctness and clarity over cleverness
- Avoid async unless explicitly requested
- Production-safe defaults only

Current project structure:
(PASTE TREE HERE)

Relevant files for this task:
(PASTE FILES HERE)

Goal of this change:
(DESCRIBE WHAT YOU WANT TO ACHIEVE)

Current behavior:
(DESCRIBE WHAT HAPPENS NOW)

Expected behavior:
(DESCRIBE WHAT SHOULD HAPPEN)
