from fastapi import APIRouter, Depends
from ...config.settings import Tags
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

router = APIRouter(
    prefix="/emails",
    tags=[Tags.emails],

)

class EmailSchema(BaseModel):
    gmail_id: str
    thread_id: str
    sender: EmailStr
    recipients: List[EmailStr]
    cc: List[EmailStr] = []
    bcc: List[EmailStr] = []
    subject: Optional[str]
    body_plain: Optional[str]
    body_html: Optional[str]
    date_sent: datetime
    labels: List[str]

    class Config:
        from_attributes = True  # allows SQLAlchemy -> Pydantic



@router.get("/")
async def read_emails():
    return [{"from": "Rick", "to": "Shane", "subject": "fix", "body": "Please fix this"}, {"username": "Morty"}]


@router.get("/count", tags=[Tags.stats])
async def read_email_count():
    return {"username": "fakecurrentuser"}


@router.get("/stats", tags=[Tags.stats])
async def read_email_stats():
    return {"username": "fakecurrentuser", "last sync": "2024-01-01T00:00:00Z"}

@router.post("/sync")
async def sync_mail(
    session: AsyncSession = Depends(get_db),
):
    gmail_messages = fetch_gmail_messages()

    for msg in gmail_messages:
        email = gmail_to_email(msg)
        await save_email(session, email)

    return {"status": "ok"}

@router.post("/gmail/sync/incremental")
async def gmail_incremental_sync(
    session: AsyncSession = Depends(get_db),
):
    await incremental_gmail_sync(
        session=session,
        gmail_service=get_gmail_service(),
        user_email="your@email.com",
    )
    return {"status": "incremental sync completed"}
