from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.gmail.auth import get_credentials
from app.gmail.client import get_gmail_service
from app.gmail.parser import fetch_and_store_email
from app.db.models import Email
from sqlalchemy.orm import Session
from sqlalchemy import text
from email import message_from_bytes
import base64

from app.db.gmail_state import (
    get_last_history_id,
    set_last_history_id,
)


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


def sync_incremental(db: Session):
    service = get_gmail_service()
    start_history_id = get_last_history_id(db)

    try:
        response = service.users().history().list(
            userId="me",
            startHistoryId=start_history_id,
            historyTypes=[
                "messageAdded",
                "labelAdded",
                "labelRemoved",
            ],
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            full_resync(db)
            return
        raise

    for h in response.get("history", []):
        for msg in h.get("messagesAdded", []):
            fetch_and_store_email(db, service, msg["message"]["id"])


def update_labels(db, gmail_id: str, label_ids: list[str]):
    email = db.query(Email).filter_by(gmail_id=gmail_id).first()
    if not email:
        return

    email.in_inbox = "INBOX" in label_ids
    db.commit()

def start_sync_log(db, sync_type):
    result = db.execute(
        text(
            """
            INSERT INTO gmail_sync_log (sync_type)
            VALUES (:t)
            RETURNING id
            """
        ),
        {"t": sync_type},
    )
    sync_id = result.fetchone()[0]
    db.commit()
    return sync_id


def finish_sync_log(db, sync_id, added, updated, success=True, error=None):
    db.execute(
        text(
            """
            UPDATE gmail_sync_log
            SET finished_at = now(),
                messages_added = :a,
                labels_updated = :u,
                success = :s,
                error = :e
            WHERE id = :id
            """
        ),
        {
            "id": sync_id,
            "a": added,
            "u": updated,
            "s": success,
            "e": error,
        },
    )
    db.commit()
