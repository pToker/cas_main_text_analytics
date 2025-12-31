from sqlalchemy import (
    Column,
    Index,
    String,
    DateTime,
    Text,
    Boolean,
    Integer
)
from app.db.base import Base


class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(String, primary_key=True)
    history_id = Column(String)
    running = Column(Boolean, default=False)
    last_started_at = Column(DateTime(timezone=True))
    last_finished_at = Column(DateTime(timezone=True))
    processed_messages = Column(Integer, default=0)
    last_error = Column(Text)

    __table_args__ = (
        Index("ix_sync_state_history_id", "history_id"),
    )