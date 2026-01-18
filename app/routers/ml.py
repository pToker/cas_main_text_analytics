from fastapi import APIRouter, Depends
from app.db.session import get_db

from app.ml.training import load_training_data, train_model, evaluate_model
from app.ml.persistence import save_model, load_model
from app.ml.utils import split_data
from app.ml.inference import load_inbox_emails, predict_labels
from app.models.label import Label
import uuid

router = APIRouter(prefix="/admin")

@router.post("/train-and-predict")
async def train_and_predict(db=Depends(get_db)):
    """TF-IDF based single label: Train a model on existing labeled emails and predict labels for inbox emails."""
    texts, labels = await load_training_data(db)
    vectorizer, clf = train_model(texts, labels)
    save_model(vectorizer, clf)

    inbox_rows, inbox_texts = await load_inbox_emails(db)
    predictions = predict_labels(vectorizer, clf, inbox_texts)

    # TODO: Remove as we don't want to store predicted labels yet
    # for email, label_name in zip(inbox_rows, predictions):
    #     db.add(
    #         Label(
    #             id=str(uuid.uuid4()),
    #             email_id=email.id,
    #             name=label_name,
    #         )
    #     )

    # await db.commit()
    return {"predicted": [{email.subject: label_name} for email, label_name in zip(inbox_rows, predictions)]}

@router.post("/train")
async def train_ml_model(db=Depends(get_db)):
    texts, labels = await load_training_data(db)
    vectorizer, clf = train_model(texts, labels)
    save_model(vectorizer, clf)
    return {"message": "Model trained successfully"}


@router.post(
        "/train-and-evaluate",
        summary="Train and evaluate ML model based on TF-IDF and LinearSVC",
        )
async def train_and_evaluate(db=Depends(get_db)):
    texts, labels = await load_training_data(db)

    (
        texts_train,
        texts_test,
        labels_train,
        labels_test,
    ) = split_data(texts, labels)

    vectorizer, clf = train_model(texts_train, labels_train)

    metrics = evaluate_model(
        vectorizer,
        clf,
        texts_test,
        labels_test,
    )

    return list({"metrics": metrics, "result_subset": [result for result in zip([message.split("\n")[0] for message in texts_test], labels_test, metrics['predictions'])][:10]})

@router.get("/predict")
async def predict_ml_labels(db=Depends(get_db)):
    vectorizer, clf = load_model()
    inbox_rows, inbox_texts = await load_inbox_emails(db)
    predictions = predict_labels(vectorizer, clf, inbox_texts)
    return {"predicted": [{email.subject: label_name} for email, label_name in zip(inbox_rows, predictions)]}