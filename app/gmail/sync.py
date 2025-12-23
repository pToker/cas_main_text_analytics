from app.gmail.client import get_gmail_service
from app.db import SessionLocal
from app.models import Email, Label, SyncState
from email.utils import parsedate_to_datetime
import base64


def get_plain_text(payload):
    if payload["mimeType"] == "text/plain":
        data = payload["body"].get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")

    for part in payload.get("parts", []):
        if part["mimeType"] == "text/plain":
            data = part["body"].get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")

    return ""


def get_label_map(service):
    """
    Returns a dict:
    {
        'Label_123': 'Finance/Taxes',
        'INBOX': 'INBOX'
    }
    """
    result = service.users().labels().list(userId="me").execute()
    return {label["id"]: label["name"] for label in result["labels"]}


def sync_gmail():
    service = get_gmail_service()
    db = SessionLocal()

    label_map = get_label_map(service)

    state = db.query(SyncState).first()

    if state:
        response = service.users().history().list(
            userId="me",
            startHistoryId=state.history_id
        ).execute()

        messages = []
        for h in response.get("history", []):
            messages.extend(h.get("messagesAdded", []))
    else:
        response = service.users().messages().list(
            userId="me",
            maxResults=50
        ).execute()
        messages = [{"message": m} for m in response.get("messages", [])]

    last_history_id = None

    for entry in messages:
        msg_id = entry["message"]["id"]

        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in msg["payload"]["headers"]
        }

        email = Email(
            id=msg["id"],
            thread_id=msg["threadId"],
            from_address=headers.get("From"),
            to_address=headers.get("To"),
            subject=headers.get("Subject"),
            date=parsedate_to_datetime(headers.get("Date")),
            body=get_plain_text(msg["payload"]),
        )

        db.merge(email)

        # store label *names* instead of IDs
        for label_id in msg.get("labelIds", []):
            label_name = label_map.get(label_id, label_id)

            db.merge(
                Label(
                    id=f"{msg_id}:{label_name}",
                    name=label_name,
                    email=email
                )
            )

        last_history_id = msg.get("historyId")

    if last_history_id:
        db.merge(
            SyncState(
                id="gmail",
                history_id=last_history_id
            )
        )

    db.commit()
    db.close()
