import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

async def commit_or_rollback(db, *, context: dict):
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.error(
            "DB transaction rolled back",
            exc_info=True,
            extra=context,
        )
        raise
