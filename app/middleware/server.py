from starlette.middleware.base import BaseHTTPMiddleware
import os
from fastapi import Request

class ServerHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['Server'] = os.environ.get('SERVER_HEADER', '')
        return response
