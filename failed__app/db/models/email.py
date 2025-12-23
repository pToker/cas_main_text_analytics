from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from failed__app.db.base import Base


class EmailDB(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("gmail_id", name="uq_email_gmail_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    gmail_id: Mapped[str] = mapped_column(String(128), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False)

    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipients: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    cc: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    bcc: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    subject: Mapped[str | None] = mapped_column(String(998))
    body_plain: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)

    date_sent: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    labels: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
