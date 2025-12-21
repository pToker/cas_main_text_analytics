from dotenv import load_dotenv
import os

load_dotenv('ENV')  # Load environment variables from .env file
pg_user_mailapp_pw = os.getenv("PG_USER_MAILAPP")
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+psycopg2://mailapp:{pg_user_mailapp_pw}@localhost/mail_classifier")