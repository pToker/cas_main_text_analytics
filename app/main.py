from fastapi import FastAPI
from app.gmail.sync import sync_gmail

app = FastAPI()

@app.post("/sync")
def sync():
    sync_gmail()
    return {"status": "ok"}
