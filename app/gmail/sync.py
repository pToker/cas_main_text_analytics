from googleapiclient.discovery import build
from app.gmail.auth import get_credentials
from app.db.models import Email
from sqlalchemy.orm import Session
from email import message_from_bytes
import base64

def sync_inbox(db: Session):
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"]
    ).execute()

    for msg in results.get("messages", []):
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="raw"
        ).execute()

        raw = base64.urlsafe_b64decode(full["raw"])
        email_msg = message_from_bytes(raw)

        subject = email_msg.get("Subject", "")
        sender = email_msg.get("From", "")

        body = ""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = email_msg.get_payload(decode=True).decode(errors="ignore")

        cleaned = body[:4000]  # temporary, improve later

        exists = db.query(Email).filter_by(gmail_id=msg["id"]).first()
        if exists:
            continue

        db.add(Email(
            gmail_id=msg["id"],
            subject=subject,
            sender=sender,
            body=body,
            cleaned_text=cleaned
        ))

    db.commit()

