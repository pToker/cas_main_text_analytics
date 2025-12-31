import logging
import logging.config
import os
from pathlib import Path

# Determine log level from environment variable. Default to WARNING if not set.
LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "WARNING").upper(), logging.WARNING)


APP_DIR = Path(__file__).parent.resolve()
BASE_DIR = APP_DIR.parent
LOG_DIR = Path(os.getenv("LOG_DIR", APP_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # important for uvicorn / sqlalchemy
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_FILE),
            "when": "W6", # every sunday
            "backupCount": 52, # keep a year of logs
            "encoding": "utf-8",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": LOG_LEVEL,
        "filename": "app.log",
        "filemode": "a",
    },
    "loggers": {
        # Reduce noisy libs if needed
        "uvicorn.access": {"level": "WARNING"},
        "sqlalchemy.engine": {"level": "WARNING"},
        "asyncpg": {"level": "WARNING"},
        "googleapiclient": {"level": "WARNING"},
        "app": {"level": LOG_LEVEL},
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)