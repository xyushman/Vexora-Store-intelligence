# PROMPT: Load a POS CSV (line-item grain) into a pos_transactions table, aggregated by order/invoice
# CHANGES MADE: Created ingest_pos_csv service

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert
import pytz
from datetime import datetime
from ..models.pos import POSTransaction

async def ingest_pos_csv(db: AsyncSession, csv_path: str, store_id: str) -> dict:
    try:
        df = pd.read_csv(csv_path)
        
        if 'invoice_number' in df.columns:
            txn_col = 'invoice_number'
        else:
            txn_col = 'order_id'
            
        df['datetime_str'] = df['order_date'] + ' ' + df['order_time']
        tz_ist = pytz.timezone('Asia/Kolkata')
        
        def parse_to_utc(dt_str):
            dt = datetime.strptime(dt_str, '%d-%m-%Y %H:%M:%S')
            dt_ist = tz_ist.localize(dt)
            return dt_ist.astimezone(pytz.utc)

        df['timestamp_utc'] = df['datetime_str'].apply(parse_to_utc)
        
        amt_col = 'basket_value' if 'basket_value' in df.columns else 'total_amount'
        qty_col = 'quantity' if 'quantity' in df.columns else 'qty'
        if qty_col not in df.columns:
            df[qty_col] = 1 # default if missing
            
        grouped = df.groupby(txn_col).agg({
            'timestamp_utc': 'first',
            amt_col: 'sum',
            qty_col: 'sum',
            txn_col: 'count'
        }).rename(columns={txn_col: 'line_count'})
        
        loaded = 0
        skipped = 0
        
        for txn_id, row in grouped.iterrows():
            stmt = insert(POSTransaction).values(
                transaction_id=str(txn_id),
                store_id=store_id,
                timestamp_utc=row['timestamp_utc'],
                basket_value=float(row[amt_col]),
                line_count=int(row['line_count']),
                quantity=int(row[qty_col])
            ).on_conflict_do_nothing(index_elements=['transaction_id'])
            
            result = await db.execute(stmt)
            if result.rowcount > 0:
                loaded += 1
            else:
                skipped += 1
                
        await db.commit()
        return {"loaded": loaded, "skipped": skipped}
    except Exception as e:
        return {"error": str(e)}
