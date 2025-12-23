from sqlalchemy.orm import Session
from sqlalchemy import text

def get_last_history_id(db: Session) -> str:
    result = db.execute(
        text(
            "SELECT last_history_id FROM gmail_sync_state WHERE id = TRUE"
        )
    ).fetchone()
    return result[0]


def set_last_history_id(db: Session, history_id: str):
    db.execute(
        text(
            """
            UPDATE gmail_sync_state
            SET last_history_id = :hid,
                updated_at = now()
            WHERE id = TRUE
            """
        ),
        {"hid": history_id},
    )
    db.commit()
