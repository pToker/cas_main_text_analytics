from sqlalchemy.ext.asyncio import AsyncSession
from failed__app.domain.email import Email
from failed__app.db.models.email import EmailDB


async def save_email(session: AsyncSession, email: Email) -> EmailDB:
    db_email = EmailDB(
        gmail_id=email.gmail_id,
        thread_id=email.thread_id,
        sender=email.sender,
        recipients=email.recipients,
        cc=email.cc,
        bcc=email.bcc,
        subject=email.subject,
        body_plain=email.body_plain,
        body_html=email.body_html,
        date_sent=email.date_sent,
        labels=email.labels,
    )

    session.add(db_email)
    await session.commit()
    await session.refresh(db_email)
    return db_email
