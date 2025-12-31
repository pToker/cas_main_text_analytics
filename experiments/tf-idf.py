from sqlalchemy import select, func
from app.models.email import Email
from app.models.label import Label
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import numpy as np
import joblib

SEMANTIC_LABELS = ['debit', 'work', 'personal', 'spam', 'newsletter']

stmt = (
    select(
        Email.id,
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

y = [r.label for r in rows]



vectorizer = TfidfVectorizer(
    lowercase=True,
    max_features=50_000,
    ngram_range=(1, 2),
    stop_words="english",  # or "german" if most mail is German
    min_df=5,
    max_df=0.9,
)



clf = LinearSVC(
    class_weight="balanced",
)

X = vectorizer.fit_transform(texts)
clf.fit(X, y)

stmt = (
    select(Email.id, Email.subject, Email.body)
    .join(Label)
    .where(Label.name == "INBOX")
)

inbox_rows = (await db.execute(stmt)).all()

texts_inbox = [
    f"{r.subject or ''}\n{r.body or ''}"
    for r in inbox_rows
]
X_inbox = vectorizer.transform(texts_inbox)
predicted_labels = clf.predict(X_inbox)

scores = clf.decision_function(X_inbox)



THRESHOLD = 0.2

final_labels = []
for score_row, label in zip(scores, predicted_labels):
    if np.max(score_row) < THRESHOLD:
        final_labels.append("NEEDS_NEW_LABEL")
    else:
        final_labels.append(label)





# persist the model and vectorizer
joblib.dump(vectorizer, "models/tfidf.joblib")
joblib.dump(clf, "models/classifier.joblib")



# persist predicted labels back to the database

# from app.models.label import Label
# import uuid

# for email, label_name in zip(inbox_rows, final_labels):
#     db.add(
#         Label(
#             id=str(uuid.uuid4()),
#             email_id=email.id,
#             name=label_name,
#         )
#     )

# await db.commit()