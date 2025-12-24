from app.gmail.client import get_gmail_service
from app.db import SessionLocal
from app.models import Email, Label, SyncState
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import base64
import time
from googleapiclient.errors import HttpError
from sqlalchemy.exc import OperationalError


MAX_RETRIES = 5


def safe_parse_date(value):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except ValueError:
        return None


def gmail_call(func):
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except HttpError as e:
            if e.resp.status in (429, 500, 503):
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError("Gmail API retry limit exceeded")


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
    result = gmail_call(
        lambda: service.users().labels().list(userId="me").execute()
    )
    return {label["id"]: label["name"] for label in result["labels"]}


def acquire_sync_lock(db):
    """
    Atomically acquire the sync lock.
    Returns SyncState if acquired, None if already running.
    """
    try:
        state = (
            db.query(SyncState)
            .with_for_update()
            .first()
        )

        if not state:
            state = SyncState(id="gmail")
            db.add(state)
            db.flush()

        if state.running:
            return None

        state.running = True
        state.last_started_at = datetime.utcnow()
        state.processed_messages = 0
        state.last_error = None

        db.commit()
        return state

    except OperationalError:
        db.rollback()
        return None


def release_sync_lock(db, state):
    state.running = False
    state.last_finished_at = datetime.now(tz=timezone.utc)
    db.commit()


def store_message(service, db, label_map, msg_id):
    msg = gmail_call(
        lambda: service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()
    )

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    email = Email(
        id=msg["id"],
        thread_id=msg["threadId"],
        from_address=headers.get("From"),
        to_address=headers.get("To"),
        subject=headers.get("Subject"),
        date=safe_parse_date(headers.get("Date")),
        body=get_plain_text(msg["payload"]),
    )

    db.merge(email)

    for label_id in msg.get("labelIds", []):
        label_name = label_map.get(label_id, label_id)
        db.merge(
            Label(
                id=f"{msg_id}:{label_name}",
                name=label_name,
                email=email
            )
        )


def sync_gmail():
    db = SessionLocal()
    state = acquire_sync_lock(db)

    if state is None:
        db.close()
        return

    try:
        service = get_gmail_service()
        label_map = get_label_map(service)

        if state.history_id is None:
            # INITIAL FULL SYNC
            next_page_token = None

            while True:
                response = gmail_call(
                    lambda: service.users().messages().list(
                        userId="me",
                        pageToken=next_page_token,
                        maxResults=500
                    ).execute()
                )

                for msg in response.get("messages", []):
                    store_message(service, db, label_map, msg["id"])
                    state.processed_messages += 1

                # SAFE COMMIT POINT
                db.commit()
                state.history_id = response.get("historyId")
                db.commit()

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        else:
            # INCREMENTAL SYNC
            response = gmail_call(
                lambda: service.users().history().list(
                    userId="me",
                    startHistoryId=state.history_id
                ).execute()
            )

            for h in response.get("history", []):
                for added in h.get("messagesAdded", []):
                    store_message(
                        service,
                        db,
                        label_map,
                        added["message"]["id"],
                    )
                    state.processed_messages += 1

                # SAFE COMMIT AFTER EACH HISTORY BATCH
                db.commit()
                if h.get("id"):
                    state.history_id = h["id"]
                    db.commit()

    except Exception as e:
        state.last_error = str(e)
        db.commit()
        raise

    finally:
        release_sync_lock(db, state)
        db.close()
