from fastapi import APIRouter, Depends
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import SyncState

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
async def sync_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        sql_text("SELECT * FROM sync_state LIMIT 1")
    )
    state = result.fetchone()

    if not state:
        return {
            "running": False,
            "last_started_at": None,
            "last_finished_at": None,
            "processed_messages": 0,
            "history_id": None,
            "last_error": None,
        }

    return {
        "running": state.running,
        "last_started_at": state.last_started_at,
        "last_finished_at": state.last_finished_at,
        "processed_messages": state.processed_messages,
        "history_id": state.history_id,
        "last_error": state.last_error,
    }
