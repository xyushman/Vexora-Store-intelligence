import os
import sqlite3
import csv
import random
import logging
from datetime import datetime, timedelta
import aiosqlite

logger = logging.getLogger("store_intelligence")

DB_PATH = os.getenv("DB_PATH", "./db/store_intelligence.db")
DATA_DIR = os.getenv("DATA_DIR", "./data/")

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA foreign_keys=ON")
    
    conn.executescript("""
CREATE TABLE IF NOT EXISTS events (
    event_id     TEXT PRIMARY KEY,
    store_id     TEXT NOT NULL,
    camera_id    TEXT NOT NULL,
    visitor_id   TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    zone_id      TEXT,
    dwell_ms     INTEGER DEFAULT 0,
    is_staff     INTEGER NOT NULL,
    confidence   REAL NOT NULL,
    queue_depth  INTEGER,
    sku_zone     TEXT,
    session_seq  INTEGER,
    ingested_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);



CREATE TABLE IF NOT EXISTS conversion_history (
    store_id         TEXT NOT NULL,
    date             TEXT NOT NULL,
    conversion_rate  REAL NOT NULL,
    PRIMARY KEY (store_id, date),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);

CREATE TABLE IF NOT EXISTS anomaly_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id      TEXT NOT NULL,
    anomaly_type  TEXT NOT NULL,
    severity      TEXT NOT NULL,
    detected_at   TEXT NOT NULL,
    resolved_at   TEXT,
    metadata      TEXT,
    FOREIGN KEY (store_id) REFERENCES stores(id)
);

CREATE INDEX IF NOT EXISTS idx_events_store_ts   ON events(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_visitor     ON events(store_id, visitor_id, event_type);

CREATE INDEX IF NOT EXISTS idx_anomaly_store      ON anomaly_log(store_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_pos_store_ts       ON pos_transactions(store_id, timestamp_utc);
    """)
    
    stores = ["ST1008", "STORE_BLR_003", "STORE_MUM_001", "STORE_DEL_004", "STORE_HYD_005"]
    today = datetime.now()
    for d in range(7, 0, -1):
        dt = (today - timedelta(days=d)).strftime('%Y-%m-%d')
        for s in stores:
            rate = round(0.18 + random.uniform(-0.04, 0.04), 4)
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO conversion_history (store_id, date, conversion_rate) VALUES (?, ?, ?)",
                    (s, dt, rate)
                )
            except sqlite3.Error:
                pass
    conn.commit()
    conn.close()

KNOWN_STAFF_EMPLOYEE_CODES = {'ST1008': ['CL2063','CL2727','CL1997','CL2541','CL2680']}

def load_pos_transactions():
    import pandas as pd
    pos_file = os.path.join(DATA_DIR, "pos_transactions.csv")
    if not os.path.exists(pos_file):
        logger.warning(f"POS transactions file not found: {pos_file}")
        return
        
    try:
        df = pd.read_csv(pos_file)
        df['timestamp'] = pd.to_datetime(df['order_date'] + ' ' + df['order_time'], format='%d-%m-%Y %H:%M:%S').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        unique_orders = df.groupby('order_id').first().reset_index()
        
        conn = sqlite3.connect(DB_PATH)
        count = 0
        for _, row in unique_orders.iterrows():
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO pos_transactions (txn_id, store_id, timestamp, basket_value_inr) VALUES (?, ?, ?, ?)",
                    (str(row['order_id']), str(row['store_id']), row['timestamp'], float(row['total_amount']))
                )
                count += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        
        min_date = df['timestamp'].min()
        max_date = df['timestamp'].max()
        logger.info(f"Loaded {len(df)} POS transactions, {count} unique orders, date range {min_date} to {max_date}")
    except Exception as e:
        logger.warning(f"Failed to load POS transactions: {e}")

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        yield db
