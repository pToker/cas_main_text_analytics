from fastapi import FastAPI, BackgroundTasks
from app.gmail.sync import sync_gmail
from app.routers.sync import router as sync_router
from app.config import setup_logging
from dotenv import load_dotenv
import os

load_dotenv()

setup_logging()

app = FastAPI(title="Gmail Sync Service")

app.include_router(sync_router)


@app.post("/sync/run")
def run_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gmail)
    return {"status": "sync started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), log_level=os.getenv("LOG_LEVEL", "info"))