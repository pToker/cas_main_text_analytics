from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv("ENV")
pwd = os.getenv("PG_USER_MAILAPP")


class Tags(Enum):
    emails = "Communication/Emails"
    db = "Database"
    stats = "Statistics"

DATABASE_URL = f"postgresql+psycopg2://mailapp:{pwd}@localhost/mail_classifier"