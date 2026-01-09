

from sklearn.model_selection import train_test_split
from nltk.corpus import stopwords
from app.ml.config import TRAINING_TEST_SPLIT



def split_data(texts, labels, test_size=TRAINING_TEST_SPLIT, seed=42):
    return train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=seed,
        stratify=labels,   # IMPORTANT for imbalanced labels
    )


def get_stopwords(languages: list[str] = ["english","german"]) -> set[str]:
    return [stopword for language in languages for stopword in stopwords.words(language)]