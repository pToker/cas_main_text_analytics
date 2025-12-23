from failed__app.db.models.gmail_sync_state import GmailSyncState
from failed__app.services.gmail_mapper import gmail_to_email
from failed__app.repositories.email_repository import save_email


async def full_gmail_sync(
    session,
    gmail_service,
    user_email: str,
):
    response = gmail_service.users().messages().list(
        userId="me",
        maxResults=500,
    ).execute()

    messages = response.get("messages", [])
    latest_history_id = None

    for msg in messages:
        full_msg = gmail_service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full",
        ).execute()

        email = gmail_to_email(full_msg)
        await save_email(session, email)
        latest_history_id = full_msg["historyId"]

    session.add(
        GmailSyncState(
            user_email=user_email,
            last_history_id=latest_history_id,
        )
    )
    await session.commit()
