import os
from app.routers import emails
from app.logging_config import setup_logging
from app.middleware.server import ServerHeaderMiddleware
from app.routers import sync
from app.routers import ml
from app.routers.admin import db as admin_db
from fastapi import FastAPI


setup_logging()


app = FastAPI(title="Life Terminal", swagger_ui_parameters={"syntaxHighlight": {"theme": "monokai"}})
app.add_middleware(ServerHeaderMiddleware)

# include routers
app.include_router(sync.router)
app.include_router(ml.router)
app.include_router(admin_db.router)
app.include_router(emails.router)