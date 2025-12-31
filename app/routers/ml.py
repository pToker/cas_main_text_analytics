from fastapi import APIRouter, Depends
from app.db.session import get_db

from app.ml.training import load_training_data, train_model
from app.ml.persistence import save_model, load_model
from app.ml.inference import load_inbox_emails, predict_labels
from app.models.label import Label
import uuid

router = APIRouter(prefix="/admin")

@router.post("/train-and-predict")
async def train_and_predict(db=Depends(get_db)):
    texts, labels = await load_training_data(db)
    vectorizer, clf = train_model(texts, labels)
    save_model(vectorizer, clf)

    inbox_rows, inbox_texts = await load_inbox_emails(db)
    predictions = predict_labels(vectorizer, clf, inbox_texts)

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

