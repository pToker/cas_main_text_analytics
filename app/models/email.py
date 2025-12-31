from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True)
    thread_id = Column(String, index=True)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String)
    body = Column(Text)
    date_sent = Column(DateTime(timezone=True), index=True)

    labels = relationship("Label", back_populates="email", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_emails_thread_date", "thread_id", "date_sent"),
    )