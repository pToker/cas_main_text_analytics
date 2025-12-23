import asyncio

from failed__app.db.session import async_session_factory
from failed__app.services.gmail_sync import incremental_gmail_sync
from failed__app.services.gmail_full_sync import full_gmail_sync
from failed__app.services.gmail_auth import get_gmail_service


async def run():
    gmail_service = get_gmail_service()

    async with async_session_factory() as session:
        try:
            await incremental_gmail_sync(
                session=session,
                gmail_service=gmail_service,
                user_email="your@email.com",
            )
        except RuntimeError as e:
            if "full resync" in str(e).lower():
                await full_gmail_sync(
                    session=session,
                    gmail_service=gmail_service,
                    user_email="your@email.com",
                )
            else:
                raise


if __name__ == "__main__":
    asyncio.run(run())
