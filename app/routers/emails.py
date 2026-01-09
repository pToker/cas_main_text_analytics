from fastapi import APIRouter
from app.ml.data import fetch_labeled_emails, build_label_vocab, prepare_training_data
from app.ml.train import train_model
from app.ml.predict import EmailLabelPredictor
import json

router = APIRouter(
    prefix='/email',
    tags=['email']
)

MODEL_DIR = "models/email_classifier"
predictor = None
id2label = None

@router.post("/train")
async def train():
    emails = await fetch_labeled_emails()
    label2id_local, id2label_local = build_label_vocab(emails)
    texts, Y = prepare_training_data(emails, label2id_local)

    model, tokenizer = train_model(texts, Y, label2id_local, output_dir=MODEL_DIR)

    # save vocab
    with open(f"{MODEL_DIR}/id2label.json", "w") as f:
        json.dump(id2label_local, f, indent=2)

    global predictor, id2label
    id2label = id2label_local
    predictor = EmailLabelPredictor(MODEL_DIR, id2label)

    return {"message": "Model trained", "num_labels": len(id2label)}

@router.post("/predict")
async def predict_email(subject: str, body: str):
    global predictor
    if predictor is None:
        # load model if not already loaded
        with open(f"{MODEL_DIR}/id2label.json") as f:
            id2label_local = json.load(f)
        from app.ml.predict import EmailLabelPredictor
        predictor = EmailLabelPredictor(MODEL_DIR, id2label_local)

    text = f"{subject}\n\n{body}"
    labels = predictor.predict(text)
    return {"predicted_labels": labels}
