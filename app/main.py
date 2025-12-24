from fastapi import FastAPI, BackgroundTasks
from app.gmail.sync import sync_gmail
from app.routers.sync import router as sync_router
from app.logging import setup_logging

setup_logging()

app = FastAPI(title="Gmail Sync Service")

app.include_router(sync_router)


@app.post("/sync/run")
def run_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gmail)
    return {"status": "sync started"}
