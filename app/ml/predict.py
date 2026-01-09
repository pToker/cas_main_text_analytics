# app/ml/predict.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

class EmailLabelPredictor:
    def __init__(self, model_dir, id2label):
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()
        self.id2label = id2label

    @torch.no_grad()
    def predict(self, text, threshold=0.5):
        encoding = self.tokenizer(text, truncation=True, padding='max_length', max_length=512, return_tensors='pt')
        outputs = self.model(**encoding)
        probs = torch.sigmoid(outputs.logits).squeeze(0).numpy()
        labels = [self.id2label[i] for i, p in enumerate(probs) if p >= threshold]
        if len(labels) == 0:
            labels = ["needs_new_label"]
        return labels
