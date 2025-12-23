from sqlalchemy.ext.asyncio import AsyncSession
from failed__app.db.models.gmail_sync_state import GmailSyncState
from failed__app.services.gmail_history import fetch_gmail_history, HistoryExpiredError
from failed__app.services.gmail_messages import fetch_gmail_message
from failed__app.services.gmail_mapper import gmail_to_email
from failed__app.repositories.email_repository import save_email


async def incremental_gmail_sync(
    session: AsyncSession,
    gmail_service,
    user_email: str,
):
    sync_state = await session.get(GmailSyncState, {"user_email": user_email})

    if not sync_state:
        raise RuntimeError("No initial historyId found – run full sync first")

    try:
        history, new_history_id = fetch_gmail_history(
            gmail_service=gmail_service,
            user_id="me",
            start_history_id=sync_state.last_history_id,
        )
    except HistoryExpiredError:
        raise RuntimeError("History expired – full resync required")

    for record in history:
        for msg in record.get("messagesAdded", []):
            message_id = msg["message"]["id"]
            gmail_msg = fetch_gmail_message(gmail_service, "me", message_id)
            email = gmail_to_email(gmail_msg)
            await save_email(session, email)

    sync_state.last_history_id = new_history_id
    await session.commit()
