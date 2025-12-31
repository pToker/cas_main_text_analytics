import numpy as np
from sqlalchemy import select

from app.models.email import Email
from app.models.label import Label
from app.ml.config import CONFIDENCE_THRESHOLD


async def load_inbox_emails(db):
    stmt = (
        select(Email.id, Email.subject, Email.body)
        .join(Label)
        .where(Label.name == "INBOX")
    )

    rows = (await db.execute(stmt)).all()

    texts = [
        f"{r.subject or ''}\n{r.body or ''}"
        for r in rows
    ]

    return rows, texts


def predict_labels(vectorizer, clf, texts):
    X = vectorizer.transform(texts)
    scores = clf.decision_function(X)
    labels = clf.classes_

    results = []

    for row_scores in scores:
        best_idx = int(np.argmax(row_scores))
        best_score = row_scores[best_idx]

        if best_score < CONFIDENCE_THRESHOLD:
            results.append("NEEDS_NEW_LABEL")
        else:
            results.append(labels[best_idx])

    return results
