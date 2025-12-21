from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/sync/gmail")
def sync_gmail(db: Session = Depends(get_db)):
    sync_inbox(db)
    return {"status": "ok"}


@app.post("/sync/gmail/initial")
def initial_sync(db: Session = Depends(get_db)):
    return run_initial_sync(db)
