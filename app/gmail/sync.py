import asyncio
import base64
import logging
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError

from app.gmail.client import GmailClient
from app.db.session import AsyncSessionLocal
from app.db.utils import commit_or_rollback
from app.models.email import Email
from app.models.label import Label
from app.models.sync_state import SyncState

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
MAX_CONCURRENT_EMAILS = 10

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def safe_parse_date(value: Optional[str]):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.warning("Invalid date header value=%r", value)
        return None


async def gmail_call(func):
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except HttpError as e:
            status = e.resp.status
            if status in (429, 500, 503):
                logger.warning("Gmail API transient error status=%s retry=%s", status, attempt + 1)
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error("Gmail API error status=%s message=%s", status, e)
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


async def get_label_map(service: GmailClient):
    result = await gmail_call(lambda: service.list_labels())
    return {label["id"]: label["name"] for label in result}


async def acquire_sync_lock(db: AsyncSession):
    try:
        result = await db.execute(select(SyncState).with_for_update())
        state = result.scalars().first()

        if not state:
            state = SyncState(id="gmail")
            db.add(state)
            await db.flush()

        if state.running:
            logger.info("Sync already running, exiting")
            return None

        state.running = True
        state.last_started_at = datetime.now(timezone.utc)
        state.processed_messages = 0
        state.last_error = None
        await commit_or_rollback(
            db,
            context={"sync_state_id": state.id, "action": "acquire_lock"},
        )

        logger.info("Sync started")
        return state

    except OperationalError:
        await db.rollback()
        logger.exception("Failed to acquire sync lock")
        return None


async def release_sync_lock(db: AsyncSession, state: SyncState):
    state.running = False
    state.last_finished_at = datetime.now(timezone.utc)
    await commit_or_rollback(
        db,
        context={"sync_state_id": state.id, "action": "release_lock"},
    )
    logger.info("Sync finished processed=%s", state.processed_messages)


async def store_message(service: GmailClient, db: AsyncSession, label_map, msg_id):
    msg = await gmail_call(lambda: service.get_message(msg_id))

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    email = Email(
        id=msg["id"],
        thread_id=msg["threadId"],
        from_address=headers.get("From"),
        to_address=headers.get("To", os.getenv("DEFAULT_TO_ADDRESS", "undi@sclos.ed")),
        subject=headers.get("Subject"),
        date_sent=safe_parse_date(headers.get("Date")),
        body=get_plain_text(msg["payload"]),
    )

    stmt = insert(Email).values(
        id=email.id,
        thread_id=email.thread_id,
        from_address=email.from_address,
        to_address=email.to_address,
        subject=email.subject,
        date_sent=email.date_sent,
        body=email.body,
    ).on_conflict_do_update(
        index_elements=[Email.id],
        set_={
            "thread_id": email.thread_id,
            "from_address": email.from_address,
            "to_address": email.to_address,
            "subject": email.subject,
            "date_sent": email.date_sent,
            "body": email.body,
        },
    )

    await db.execute(stmt)

    for label_id in msg.get("labelIds", []):
        label_name = label_map.get(label_id, label_id)
        stmt = insert(Label).values(
            id=f"{msg_id}:{label_name}",
            name=label_name,
            email_id=email.id,
        ).on_conflict_do_nothing()
        await db.execute(stmt)

    logger.debug("Stored message id=%s", msg_id)


async def store_message_batch(service: GmailClient, db: AsyncSession, label_map, msg_ids):
    sem = asyncio.Semaphore(MAX_CONCURRENT_EMAILS)

    async def safe_store(mid):
        async with sem:
            await store_message(service, db, label_map, mid)

    await asyncio.gather(*(safe_store(mid) for mid in msg_ids))


async def sync_gmail():
    async with AsyncSessionLocal() as db:
        state = await acquire_sync_lock(db)
        if state is None:
            return

        try:
            service = GmailClient()
            label_map = await get_label_map(service)

            if state.history_id is None:
                # Full sync
                logger.info("Full sync started")
                next_page_token = None
                while True:
                    response = await gmail_call(
                        lambda: service.list_messages(page_token=next_page_token)
                    )

                    msg_ids = [m["id"] for m in response.get("messages", [])]
                    if msg_ids:
                        await store_message_batch(service, db, label_map, msg_ids)
                        state.processed_messages += len(msg_ids)

                    try:
                        await commit_or_rollback(
                            db,
                            context={"sync_state_id": state.id, "action": "batch_store_messages"},
                        )
                    except IntegrityError as e:
                        orig = e.orig  # asyncpg exception

                        logger.error(
                            "IntegrityError while persisting email" + [ [m["id"],m["subject"], m["to"]] for m in response.get("messages", [])],
                            exc_info=True,
                            extra={
                                "account_id": account_id,
                                "history_id": history_id,
                                "gmail_id": email.gmail_id,
                                "constraint": getattr(orig, "constraint_name", None),
                                "column": getattr(orig, "column_name", None),
                                "detail": getattr(orig, "detail", None),
                            },
                        )
                        raise



                    state.history_id = response.get("historyId")
                    await commit_or_rollback(
                        db,
                        context={"sync_state_id": state.id, "action": "update_history_id"},
                    )

                    next_page_token = response.get("nextPageToken")
                    if not next_page_token:
                        break
            else:
                # Incremental sync
                logger.info("Incremental sync from history_id=%s", state.history_id)
                try:
                    response = await gmail_call(
                        lambda: service.get_history(start_history_id=state.history_id)
                    )
                except HttpError as e:
                    if e.resp.status == 404:
                        logger.warning("HistoryId expired, falling back to full sync")
                        state.history_id = None
                        await commit_or_rollback(
                            db,
                            context={"sync_state_id": state.id, "action": "reset_history_id"},
                        )
                        return await sync_gmail()
                    raise

                for h in response.get("history", []):
                    msg_ids = [added["message"]["id"] for added in h.get("messagesAdded", [])]
                    if msg_ids:
                        await store_message_batch(service, db, label_map, msg_ids)
                        state.processed_messages += len(msg_ids)

                    await commit_or_rollback(
                        db,
                        context={"sync_state_id": state.id, "action": "batch_store_messages"},
                    )
                    if h.get("id"):
                        state.history_id = h["id"]
                        await commit_or_rollback(
                            db,
                            context={"sync_state_id": state.id, "action": "update_history_id"},
                        )

        except Exception as e:
            state.last_error = str(e)
            await commit_or_rollback(
                db,
                context={"sync_state_id": state.id, "action": "record_error"},
            )
            logger.exception("Sync failed")
            raise
        finally:
            await release_sync_lock(db, state)
