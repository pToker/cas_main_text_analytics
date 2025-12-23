from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from failed__app.db.session import SessionLocal

from .routers.communcation import email
from .dependencies import get_db

app = FastAPI()

app.include_router(email.router)


@app.get("/")
async def root():
    return {"message": "Welcome to The Life"}


@app.get("/health")
@app.get("/status")
async def health_check():
    return {"status": "healthy"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/sync/gmail", status_code=202)
def sync_gmail(db: Session = Depends(get_db)):
    sync_inbox(db)
    return {"status": "ok"}


@app.post("/sync/gmail/initial")
def initial_sync(db: Session = Depends(get_db)):
    return run_initial_sync(db)
