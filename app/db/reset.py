from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def reset_email_tables(session: AsyncSession) -> None:
    """
    Deletes all data from sync_state, labels, emails.
    FK order respected.
    This is really just a convenience function for tests and development.
    """
    await session.execute(text("DELETE FROM sync_state"))
    await session.execute(text("DELETE FROM labels"))
    await session.execute(text("DELETE FROM emails"))
