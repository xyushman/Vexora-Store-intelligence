import os
TEST_DB_PATH = "test_store.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DB_PATH"] = TEST_DB_PATH
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["GEMINI_API_KEY"] = "dummy_test_key_for_gemini"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.main import app
from app.models.base import Base
from app.db.database import get_db, engine as prod_engine

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=prod_engine, class_=AsyncSession)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db_tables():
    async with prod_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                store_id TEXT,
                camera_id TEXT,
                visitor_id TEXT,
                event_type TEXT,
                timestamp TEXT,
                zone_id TEXT,
                dwell_ms INTEGER,
                is_staff INTEGER,
                confidence REAL,
                queue_depth INTEGER,
                sku_zone TEXT,
                session_seq INTEGER
            )
        """))
    yield
    async with prod_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS events"))

@pytest_asyncio.fixture(scope="function")
async def session():
    async with TestingSessionLocal() as db:
        yield db

@pytest.fixture(scope="function")
def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    del app.dependency_overrides[get_db]


