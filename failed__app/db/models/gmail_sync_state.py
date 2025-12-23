from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from failed__app.db.base import Base


class GmailSyncState(Base):
    __tablename__ = "gmail_sync_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    last_history_id: Mapped[str] = mapped_column(String(128), nullable=False)
