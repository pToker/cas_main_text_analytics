# app/ml/train.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import torch
from sklearn.model_selection import train_test_split
import numpy as np

tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")  # smaller for testing

class EmailDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        y = self.labels[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt'
        )
        return {key: val.squeeze(0) for key, val in encoding.items()}, torch.tensor(y, dtype=torch.float)

def train_model(texts, Y, label2id, output_dir="models/email_classifier"):
    num_labels = len(label2id)
    model = AutoModelForSequenceClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=num_labels,
        problem_type="multi_label_classification"
    )

    X_train, X_val, y_train, y_val = train_test_split(texts, Y, test_size=0.1, random_state=42)
    train_dataset = EmailDataset(X_train, y_train, tokenizer)
    val_dataset = EmailDataset(X_val, y_val, tokenizer)

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        learning_rate=2e-5,
        num_train_epochs=1,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="loss",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )

    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    return model, tokenizer
