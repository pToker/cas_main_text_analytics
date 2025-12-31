from sqlalchemy import (
    Column,
    Index,
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    ForeignKey,)
from sqlalchemy.orm import relationship
from app.db.base import Base



class Label(Base):
    __tablename__ = "labels"

    id = Column(String, primary_key=True)

    email_id = Column(
        String,
        ForeignKey("emails.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name = Column(String, index=True)

    email = relationship("Email", back_populates="labels")


    __table_args__ = (
        Index("ix_labels_email_id", "email_id", "name"),
    )