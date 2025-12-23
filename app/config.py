import os
from dotenv import load_dotenv

load_dotenv("ENV")

DATABASE_PWD = os.getenv("PG_USER_MAILAPP")

DATABASE_URL = f"postgresql+psycopg2://mailapp:{DATABASE_PWD}@localhost/mail_classifier"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
