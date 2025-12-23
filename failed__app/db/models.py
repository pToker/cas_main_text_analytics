from sqlalchemy import (
    Column, Text, Boolean, DateTime, JSON,
    ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from failed__app.db.base import Base
import uuid

class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_id = Column(Text, unique=True, nullable=False)
    thread_id = Column(Text)
    subject = Column(Text)
    sender = Column(Text)
    body = Column(Text)
    cleaned_text = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True))
    in_inbox = Column(Boolean, default=True)

    predicted_labels = Column(JSON)
    applied_labels = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)


class TrainingSample(Base):
    __tablename__ = "training_samples"

    email_id = Column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        primary_key=True
    )
    label_id = Column(
        Integer,
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True
    )
    value = Column(Boolean, nullable=False)
    source = Column(Text)
