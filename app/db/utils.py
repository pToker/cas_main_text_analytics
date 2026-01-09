import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def commit_or_rollback(db, *, context: dict):
    """
    # Utility function to commit a transaction or rollback in case of an error
    
    :param db: database session
    :type db: AsyncSession
    :param context: context for logging
    :type context: dict
    """
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
