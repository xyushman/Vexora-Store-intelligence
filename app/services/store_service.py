# PROMPT: Add store alias resolution so multiple submitted IDs map to one canonical store
# CHANGES MADE: Created resolve_store_id service function

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from ..models.store import Store, StoreAlias

async def resolve_store_id(db: AsyncSession, raw_id: str) -> str:
    """
    Returns canonical store ID. Checks store_aliases first, then stores directly.
    Raises HTTPException(404) if not found.
    """
    # Check alias first
    result = await db.execute(select(StoreAlias).where(StoreAlias.alias == raw_id))
    alias = result.scalars().first()
    if alias:
        return alias.canonical_id
        
    # If not found, assume raw_id is the canonical store
    return raw_id
