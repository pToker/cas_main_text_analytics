import os
from app.logging_config import setup_logging
from app.middleware.server import ServerHeaderMiddleware
from app.routers import sync
from app.routers.admin import db as admin_db
from dotenv import load_dotenv
from fastapi import FastAPI
from pathlib import Path


setup_logging()


app = FastAPI(title="Life Terminal", swagger_ui_parameters={"syntaxHighlight": {"theme": "monokai"}})
app.add_middleware(ServerHeaderMiddleware)

# include routers
app.include_router(sync.router)
app.include_router(admin_db.router)