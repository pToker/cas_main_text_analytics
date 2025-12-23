from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime


class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(String, primary_key=True, default="gmail")
    history_id = Column(String, nullable=True)

    running = Column(Boolean, default=False)
    last_started_at = Column(DateTime, nullable=True)
    last_finished_at = Column(DateTime, nullable=True)

    processed_messages = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True)
    thread_id = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    subject = Column(String)
    body = Column(Text)
    date = Column(DateTime)

    labels = relationship("Label", back_populates="email")


class Label(Base):
    __tablename__ = "labels"

    id = Column(String, primary_key=True)
    name = Column(String)
    email_id = Column(String, ForeignKey("emails.id"))

    email = relationship("Email", back_populates="labels")
