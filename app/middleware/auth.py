import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# In production, this would be loaded from .env
VALID_API_KEY = os.getenv("VEXORA_API_KEY", "vexora-test-key-123")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Key",
        )
    return api_key
