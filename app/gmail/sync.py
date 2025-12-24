import logging
import base64
import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.gmail.client import get_gmail_service
from app.db import AsyncSessionLocal
from app.models import Email, Label, SyncState

logger = logging.getLogger("gmail.sync")
MAX_RETRIES = 5
MAX_CONCURRENT_EMAILS = 10  # safe concurrency limit


def safe_parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.warning("invalid date header value=%r", value)
        return None


async def gmail_call(func):
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except HttpError as e:
            status = e.resp.status
            if status in (429, 500, 503):
                logger.warning(
                    "gmail api transient error status=%s retry=%s",
                    status,
                    attempt + 1,
                )
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(
                    "gmail api error status=%s message=%s",
                    status,
                    e,
                )
                raise
    raise RuntimeError("gmail api retry limit exceeded")


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


async def get_label_map(service):
    result = await gmail_call(lambda: service.users().labels().list(userId="me").execute())
    return {label["id"]: label["name"] for label in result["labels"]}


async def acquire_sync_lock(db: AsyncSession):
    try:
        result = await db.execute(select(SyncState).with_for_update())
        state = result.scalars().first()

        if not state:
            state = SyncState(id="gmail")
            db.add(state)
            await db.flush()

        if state.running:
            logger.info("sync already running, exiting")
            return None

        state.running = True
        state.last_started_at = datetime.now(timezone.utc)
        state.processed_messages = 0
        state.last_error = None
        await db.commit()

        logger.info("sync started")
        return state

    except OperationalError:
        await db.rollback()
        logger.exception("failed to acquire sync lock")
        return None


async def release_sync_lock(db: AsyncSession, state: SyncState):
    state.running = False
    state.last_finished_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info("sync finished processed=%s", state.processed_messages)


async def store_message(service, db: AsyncSession, label_map, msg_id):
    msg = await gmail_call(
        lambda: service.users().messages().get(userId="me", id=msg_id, format="full").execute()
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

    await db.merge(email)

    for label_id in msg.get("labelIds", []):
        label_name = label_map.get(label_id, label_id)
        await db.merge(
            Label(
                id=f"{msg_id}:{label_name}",
                name=label_name,
                email=email,
            )
        )

    logger.debug("stored message id=%s", msg_id)


async def store_message_batch(service, db: AsyncSession, label_map, msg_ids):
    sem = asyncio.Semaphore(MAX_CONCURRENT_EMAILS)

    async def safe_store(msg_id):
        async with sem:
            await store_message(service, db, label_map, msg_id)

    await asyncio.gather(*(safe_store(mid) for mid in msg_ids))


async def sync_gmail():
    async with AsyncSessionLocal() as db:
        state = await acquire_sync_lock(db)
        if state is None:
            return

        try:
            service = get_gmail_service()
            label_map = await get_label_map(service)

            if state.history_id is None:
                logger.info("full sync started")
                next_page_token = None
                while True:
                    response = await gmail_call(
                        lambda: service.users().messages().list(
                            userId="me",
                            pageToken=next_page_token,
                            maxResults=500,
                        ).execute()
                    )

                    msg_ids = [msg["id"] for msg in response.get("messages", [])]
                    if msg_ids:
                        await store_message_batch(service, db, label_map, msg_ids)
                        state.processed_messages += len(msg_ids)

                    await db.commit()
                    state.history_id = response.get("historyId")
                    await db.commit()

                    next_page_token = response.get("nextPageToken")
                    if not next_page_token:
                        break

            else:
                logger.info("incremental sync from history_id=%s", state.history_id)
                try:
                    response = await gmail_call(
                        lambda: service.users().history().list(
                            userId="me",
                            startHistoryId=state.history_id,
                        ).execute()
                    )
                except HttpError as e:
                    if e.resp.status == 404:
                        logger.warning("historyId expired, falling back to full sync")
                        state.history_id = None
                        await db.commit()
                        return await sync_gmail()
                    raise

                for h in response.get("history", []):
                    msg_ids = [added["message"]["id"] for added in h.get("messagesAdded", [])]
                    if msg_ids:
                        await store_message_batch(service, db, label_map, msg_ids)
                        state.processed_messages += len(msg_ids)

                    await db.commit()
                    if h.get("id"):
                        state.history_id = h["id"]
                        await db.commit()

        except Exception as e:
            state.last_error = str(e)
            await db.commit()
            logger.exception("sync failed")
            raise

        finally:
            await release_sync_lock(db, state)
