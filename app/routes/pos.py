# PROMPT: Expose POST /pos/ingest
# CHANGES MADE: Created pos.py router

import os
from fastapi import APIRouter, Depends, Query, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.pos_service import ingest_pos_csv
from ..services.store_service import resolve_store_id
from ..middleware.auth import verify_api_key
from ..middleware.rate_limiter import limiter

router = APIRouter()

@router.post("/pos/ingest", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def ingest_pos(
    request: Request,
    store_id: str = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    canonical_store_id = await resolve_store_id(db, store_id)
    
    os.makedirs("/tmp", exist_ok=True)
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
        
    result = await ingest_pos_csv(db, temp_path, canonical_store_id)
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return result
