from pathlib import Path
from typing import Dict, Any
import os

# Load .env automaticcally
BASE_DIR = Path(__file__).parent.resolve()

DATABASE_PWD = os.getenv("PG_USER_MAILAPP")

DATABASE_URL: str = os.getenv("DATABASE_URL", f"postgresql+asyncpg://mailapp:{DATABASE_PWD}@localhost/mail_classifier")
DATABASE_URL_ALEMBIC: str = os.getenv("DATABASE_URL_ALEMBIC", f"postgresql+psycopg2://mailapp:{DATABASE_PWD}@localhost/mail_classifier")

CREDENTIALS_FILE: Path = Path(os.getenv("CREDENTIALS_FILE", BASE_DIR / "credentials.json"))
ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "change_me_to_a_secure_key")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify",
                 "https://www.googleapis.com/auth/gmail.labels",]

def load_credentials() -> Dict[str, Any]:
    if CREDENTIALS_FILE.exists():
        import json
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    return {}

