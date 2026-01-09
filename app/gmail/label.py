from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Email, Label
from app.db import AsyncSessionLocal
from collections import Counter
import numpy as np


async def fetch_labeled_emails():
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Email)
            .options(selectinload(Email.labels))
            .where(Email.labels.any())
            .where(
                Email.labels.any(Label.name != "INBOX")
            )
        )

        result = await session.execute(stmt)
        return result.scalars().unique().all()


def build_label_vocab(emails, min_count=10):
    counter = Counter()

    for email in emails:
        for label in email.labels:
            if label.name != "INBOX":
                counter[label.name] += 1

    labels = sorted(
        name for name, count in counter.items()
        if count >= min_count
    )

    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for label, i in label2id.items()}

    return label2id, id2label