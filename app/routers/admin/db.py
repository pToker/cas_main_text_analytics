from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db, reset_email_tables
from app.config import ADMIN_API_KEY
from pydantic import SecretStr


router = APIRouter(
    prefix="/admin/db",
    tags=["admin"],
)

def check_api_key(api_key: SecretStr):
    if api_key.get_secret_value() != ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

@router.post(
    "/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all synced Gmail data",
)
async def reset_database(api_key: SecretStr, session: AsyncSession = Depends(get_db)) -> None:
    check_api_key(api_key)
    async with session.begin():
        # Reset email-related tables. more tables can be added as needed.
        await reset_email_tables(session)
