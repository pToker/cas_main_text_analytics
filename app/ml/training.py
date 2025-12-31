from sqlalchemy import select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from app.models.email import Email
from app.models.label import Label
from app.ml.config import SEMANTIC_LABELS


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




def train_model(texts, labels):
    vectorizer = TfidfVectorizer(
        lowercase=True,
        max_features=50_000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=5,
        max_df=0.9,
    )

    X = vectorizer.fit_transform(texts)

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X, labels)

    return vectorizer, clf
