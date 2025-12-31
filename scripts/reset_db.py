import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.db.reset import reset_sync_tables

logger = logging.getLogger(__name__)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await reset_sync_tables(session)

    logger.info("✅ Database reset: sync_state, labels, emails")


if __name__ == "__main__":
    asyncio.run(main())
