from dotenv import load_dotenv
import logging
import os

load_dotenv("ENV")

DATABASE_PWD = os.getenv("PG_USER_MAILAPP")

DATABASE_URL = f"postgresql+asyncpg://mailapp:{DATABASE_PWD}@localhost/mail_classifier"
DATABASE_URL_ALEMBIC = f"postgresql+psycopg2://mailapp:{DATABASE_PWD}@localhost/mail_classifier"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        filename="app.log",
        filemode="a",
    )
