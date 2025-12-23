from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class Email:
    gmail_id: str
    thread_id: str
    sender: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    subject: Optional[str]
    body_plain: Optional[str]
    body_html: Optional[str]
    date_sent: datetime
    labels: List[str]
