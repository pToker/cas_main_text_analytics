from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging

from app.gmail.sync import sync_gmail
from app.db.session import AsyncSessionLocal
from app.models.sync_state import SyncState
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/run")
def sync_emails(background_tasks: BackgroundTasks):
    """
    Trigger Gmail sync as a background task.
    """
    try:
        background_tasks.add_task(sync_gmail)
        logger.info(
            "Gmail sync task started in background",
            extra={"background_tasks": background_tasks},
        )
        return {"status": "sync started"}
    except Exception as e:
        logger.exception("Failed to start Gmail sync: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", labels=["status"])
async def sync_status():
    """
    Check current sync state.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SyncState).where(SyncState.id == "gmail"))
        state = result.scalar_one_or_none()
        if not state:
            return {"running": False, "processed_messages": 0, "last_error": None}
        return {
            "running": state.running,
            "processed_messages": state.processed_messages,
            "last_error": state.last_error,
            "last_started_at": state.last_started_at,
            "last_finished_at": state.last_finished_at,
            "history_id": state.history_id,
        }
