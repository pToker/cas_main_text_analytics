from sqlalchemy import select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from app.models.email import Email
from app.models.label import Label
from app.ml.config import SEMANTIC_LABELS
from app.ml.utils import get_stopwords
import numpy as np


async def load_training_data(db):
    stmt = (
        select(
            Email.subject,
            Email.body,
            Label.name.label("label"),
        )
        .join(Label)
        .where(Label.name.in_(SEMANTIC_LABELS))
    )

    rows = (await db.execute(stmt)).all()

    texts = [
        f"{r.subject or ''}\n{r.body or ''}"
        for r in rows
    ]
    labels = [r.label for r in rows]

    return texts, labels




def train_model(texts_train, labels_train):
    vectorizer = TfidfVectorizer(
        lowercase=True,
        max_features=50_000,
        ngram_range=(1, 2),
        stop_words=get_stopwords(),
        min_df=5,
        max_df=0.9,
    )

    X_train = vectorizer.fit_transform(texts_train)

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X_train, labels_train)

    return vectorizer, clf

def evaluate_model(vectorizer, clf, texts_test, labels_test):
    X_test = vectorizer.transform(texts_test)
    preds = clf.predict(X_test)

    accuracy = accuracy_score(labels_test, preds)

    report = classification_report(
        labels_test,
        preds,
        digits=3,
        zero_division=0,
    )

    cm = confusion_matrix(labels_test, preds)

    return {
        "accuracy": accuracy,
        "report": report,
        "confusion_matrix": cm,
        "predictions": preds,
    }



def prepare_training_data(emails, label2id):
    texts = []
    targets = []

    for email in emails:
        text = f"{email.subject or ''}\n\n{email.body or ''}"
        y = email_to_multihot(email, label2id)

        # Skip emails that lost all labels after filtering
        if y.sum() == 0:
            continue

        texts.append(text)
        targets.append(y)

    return texts, np.vstack(targets)
