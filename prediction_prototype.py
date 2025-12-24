import psycopg2
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification, AdamW
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

# -----------------------------
# 1. Load emails from PostgreSQL
# -----------------------------
conn = psycopg2.connect(
    host="localhost",
    dbname="your_db",
    user="your_user",
    password="your_pass"
)

df = pd.read_sql("SELECT id, subject, body, labels FROM emails", conn)

# Convert labels from comma-separated to list
df['labels'] = df['labels'].apply(lambda x: x.split(',') if x else [])

# -----------------------------
# 2. Prepare multi-label encoding
# -----------------------------
mlb = MultiLabelBinarizer()
y = mlb.fit_transform(df['labels'])
print("All labels:", mlb.classes_)

# -----------------------------
# 3. Train/test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df['subject'] + ' ' + df['body'], y, test_size=0.2, random_state=42
)

# -----------------------------
# 4. Dataset class
# -----------------------------
class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=512):
        self.texts = list(texts)
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt'
        )
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float)
        return item

# -----------------------------
# 5. Load tokenizer and model
# -----------------------------
tokenizer = XLMRobertaTokenizer.from_pretrained("xlm-roberta-base")
model = XLMRobertaForSequenceClassification.from_pretrained(
    "xlm-roberta-base",
    num_labels=len(mlb.classes_),
)

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# -----------------------------
# 6. DataLoaders
# -----------------------------
train_dataset = EmailDataset(X_train, y_train, tokenizer)
test_dataset = EmailDataset(X_test, y_test, tokenizer)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=8)

# -----------------------------
# 7. Optimizer and loss
# -----------------------------
optimizer = AdamW(model.parameters(), lr=2e-5)
loss_fn = torch.nn.BCEWithLogitsLoss()

# -----------------------------
# 8. Training loop (simplified)
# -----------------------------
epochs = 2
for epoch in range(epochs):
    model.train()
    total_loss = 0
    for batch in train_loader:
        optimizer.zero_grad()
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
    print(f"Epoch {epoch+1}, Loss: {total_loss/len(train_loader):.4f}")

# -----------------------------
# 9. Prediction & evaluation
# -----------------------------
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        logits = model(input_ids, attention_mask=attention_mask).logits
        preds = torch.sigmoid(logits) > 0.5  # Threshold for multi-label
        all_preds.append(preds.cpu())
        all_labels.append(labels.cpu())

all_preds = torch.vstack(all_preds).numpy()
all_labels = torch.vstack(all_labels).numpy()

f1 = f1_score(all_labels, all_preds, average='micro')
print("F1 Score:", f1)

# -----------------------------
# 10. Predict new inbox emails
# -----------------------------
def predict_labels(texts, model, tokenizer, threshold=0.5):
    model.eval()
    encodings = tokenizer(texts, truncation=True, padding=True, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**encodings).logits
        probs = torch.sigmoid(logits)
        labels_pred = (probs > threshold).cpu().numpy()
    return [mlb.classes_[i] for i in range(len(mlb.classes_)) if labels_pred[0][i]]

# Example:
new_email_text = ["Hello team, please review the attached report."]
predicted = predict_labels(new_email_text, model, tokenizer)
print("Predicted labels:", predicted)



########################################### with embedding but somehow much shortern than expected ###########################################

















import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# 1. Get embeddings for all labeled emails
# -----------------------------
def get_embeddings(texts, model, tokenizer, device, batch_size=8):
    model.eval()
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        enc = tokenizer(batch_texts, truncation=True, padding=True, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**enc, output_hidden_states=True)
            # CLS token embedding (first token)
            cls_emb = outputs.hidden_states[-1][:, 0, :].cpu().numpy()
            embeddings.append(cls_emb)
    return np.vstack(embeddings)

# Embeddings for all labeled emails
all_texts = df['subject'] + ' ' + df['body']
all_embeddings = get_embeddings(all_texts.tolist(), model, tokenizer, device)

# -----------------------------
# 2. Compute centroids per label
# -----------------------------
label_centroids = {}
for i, label in enumerate(mlb.classes_):
    idxs = np.where(y[:, i] == 1)[0]
    if len(idxs) > 0:
        label_centroids[label] = all_embeddings[idxs].mean(axis=0)
    else:
        label_centroids[label] = np.zeros(all_embeddings.shape[1])

# -----------------------------
# 3. Predict new email + "needs new label"
# -----------------------------
def predict_labels_with_outlier(texts, model, tokenizer, mlb, label_centroids, device, threshold=0.5, outlier_thresh=0.7):
    # Step 1: Predict standard labels
    model.eval()
    encodings = tokenizer(texts, truncation=True, padding=True, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**encodings).logits
        probs = torch.sigmoid(logits)
        labels_pred = (probs > threshold).cpu().numpy()
    
    # Step 2: Get embeddings
    embeddings = get_embeddings(texts, model, tokenizer, device)

    results = []
    for i, text in enumerate(texts):
        assigned_labels = [mlb.classes_[j] for j, val in enumerate(labels_pred[i]) if val == 1]
        
        # Compute cosine similarity to all label centroids
        sims = [cosine_similarity([embeddings[i]], [centroid])[0][0] for centroid in label_centroids.values()]
        max_sim = max(sims)
        
        if max_sim < outlier_thresh:
            assigned_labels.append("needs new label")
        
        results.append(assigned_labels)
    
    return results

# -----------------------------
# 4. Example
# -----------------------------
new_emails = [
    "Hello team, please review the attached report.",
    "Random text that probably doesn't fit existing categories."
]

predicted_labels = predict_labels_with_outlier(new_emails, model, tokenizer, mlb, label_centroids, device)
for email, labels in zip(new_emails, predicted_labels):
    print("Email:", email)
    print("Predicted labels:", labels)
    print()
