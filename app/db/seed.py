# PROMPT: Seed the known aliases on startup
# CHANGES MADE: Created seed.py with STORES and ALIASES

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.store import Store, StoreAlias
from .database import AsyncSessionLocal

STORES = [{"id": "ST1008", "name": "Purplle Brigade Bangalore", "city": "Bangalore"}]
ALIASES = [
    {"alias": "ST1008",          "canonical_id": "ST1008"},
    {"alias": "STORE_BLR_002",   "canonical_id": "ST1008"},
    {"alias": "Brigade_Bangalore","canonical_id": "ST1008"},
]

async def seed_stores():
    async with AsyncSessionLocal() as db:
        for s in STORES:
            res = await db.execute(select(Store).where(Store.id == s["id"]))
            if not res.scalars().first():
                db.add(Store(**s))
        
        for a in ALIASES:
            res = await db.execute(select(StoreAlias).where(StoreAlias.alias == a["alias"]))
            if not res.scalars().first():
                db.add(StoreAlias(**a))
                
        await db.commit()
