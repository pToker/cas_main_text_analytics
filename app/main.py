from fastapi import FastAPI, BackgroundTasks
from app.gmail.sync import sync_gmail
from app.db import SessionLocal
from app.models import SyncState

app = FastAPI()


@app.post("/sync", status_code=202)
def sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gmail)
    return {"status": "sync started"}


@app.get("/status")
def status():
    db = SessionLocal()
    state = db.query(SyncState).first()
    db.close()

    if not state:
        return {"status": "never run"}

    return {
        "running": state.running,
        "processed_messages": state.processed_messages,
        "last_started_at": state.last_started_at,
        "last_finished_at": state.last_finished_at,
        "last_error": state.last_error,
    }
