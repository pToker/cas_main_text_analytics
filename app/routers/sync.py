from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import SyncState

router = APIRouter(prefix="/sync", tags=["sync"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/status")
def sync_status(db: Session = Depends(get_db)):
    state = db.query(SyncState).first()

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
