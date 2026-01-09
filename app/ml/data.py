# app/ml/data.py
from collections import Counter
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models.email import Email
from app.models.label import Label

async def fetch_labeled_emails():
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Email)
            .options(selectinload(Email.labels))
            .where(Email.labels.any())
            .where(Email.labels.any(Label.name != "INBOX"))
        )
        result = await session.execute(stmt)
        return result.scalars().unique().all()

def build_label_vocab(emails, min_count=10):
    counter = Counter()
    for email in emails:
        for label in email.labels:
            if label.name != "INBOX":
                counter[label.name] += 1

    labels = sorted(name for name, count in counter.items() if count >= min_count)
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for label, i in label2id.items()}
    return label2id, id2label

def email_to_multihot(email, label2id):
    y = np.zeros(len(label2id), dtype=np.float32)
    for label in email.labels:
        if label.name in label2id:
            y[label2id[label.name]] = 1.0
    return y


def prepare_training_data(emails, label2id):
    texts = []
    targets = []

    for email in emails:
        text = f"{email.subject or ''}\n\n{email.body or ''}"
        y = email_to_multihot(email, label2id)
        if y.sum() == 0:
            continue
        texts.append(text)
        targets.append(y)

    return texts, np.vstack(targets)
