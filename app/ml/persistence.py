import joblib
from pathlib import Path
from app.ml.config import MODEL_DIR


def save_model(vectorizer, clf):
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

    joblib.dump(vectorizer, f"{MODEL_DIR}/vectorizer.joblib")
    joblib.dump(clf, f"{MODEL_DIR}/classifier.joblib")


def load_model():
    vectorizer = joblib.load(f"{MODEL_DIR}/vectorizer.joblib")
    clf = joblib.load(f"{MODEL_DIR}/classifier.joblib")
    return vectorizer, clf
