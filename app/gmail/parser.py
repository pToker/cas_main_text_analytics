from email import message_from_bytes
import base64
from app.db.models import Email
from app.gmail.cleaner import clean_email

def fetch_and_store_email(db, service, gmail_id: str):
    ...
    


def fetch_and_store_email(db, service, gmail_id: str):
    exists = db.query(Email).filter_by(gmail_id=gmail_id).first()
    if exists:
        return

    raw_msg = service.users().messages().get(
        userId="me",
        id=gmail_id,
        format="raw",
    ).execute()

    raw = base64.urlsafe_b64decode(raw_msg["raw"])
    msg = message_from_bytes(raw)

    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    
    raw_body = extract_body(msg)
    cleaned = clean_email(raw_body)

    email = Email(
        gmail_id=gmail_id,
        subject=subject,
        sender=sender,
        body=raw_body,
        cleaned_text=cleaned,
    )

    db.add(email)
    db.commit()
