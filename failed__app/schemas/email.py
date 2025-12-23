from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


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
