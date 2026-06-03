# PROMPT: Set up SQLAlchemy async engine with SQLite WAL
# CHANGES MADE: Created database.py with get_db dependency

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

DB_PATH = os.getenv("DB_PATH", "./db/store_intelligence.db")
abs_db_path = os.path.abspath(DB_PATH)
# Ensure 4 slashes for absolute paths in SQLAlchemy sqlite URLs
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{abs_db_path}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
