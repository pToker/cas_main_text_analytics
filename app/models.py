from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True)
    thread_id = Column(String, index=True)
    from_address = Column(String)
    to_address = Column(String)
    subject = Column(String)
    date = Column(DateTime, index=True)
    body = Column(Text)

    labels = relationship("Label", back_populates="email", cascade="all, delete")

    __table_args__ = (
        Index("ix_emails_thread_date", "thread_id", "date"),
    )


class Label(Base):
    __tablename__ = "labels"

    id = Column(String, primary_key=True)
    name = Column(String, index=True)

    email_id = Column(
        String,
        ForeignKey("emails.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    email = relationship("Email", back_populates="labels")


class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(String, primary_key=True)
    history_id = Column(String)
    running = Column(Boolean, default=False)
    last_started_at = Column(DateTime)
    last_finished_at = Column(DateTime)
    processed_messages = Column(Integer, default=0)
    last_error = Column(Text)
