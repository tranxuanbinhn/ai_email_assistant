import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
def get_last_sync_timestamp_pg(db_session:Session, default_days_back:int = 3) -> int:
    query = text("SELECT value FROM system_states WHERE key = :key")
    result = db_session.execute(query, {"key": "gmail_last_sync"}).fetchone()

    if result and str(result[0].isdigit()):
        return int(result[0])
    return int(time.time()) - (default_days_back * 24 * 3600)

def update_last_sync_timestamp_pg(db_session:Session, timestamp:int):
    query = text("""
    INSERT INTO system_states (key, value, updated_at)
    VALUES (:key, :value, CURRENT_TIMESTAMP)
    ON CONFLICT (key) DO UPDATE
    SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
""")
    db_session.execute(query, {"key":"gmail_last_sync","value":str(timestamp)})
    db_session.commit()

def save_processed_id(db_session:Session, msg_id:str):
    query = text("""
    INSERT INTO processed_emails (message_id, processed_at)
    VALUES (:msg_id, CURRENT_TIMESTAMP)
    ON CONFLICT (message_id) DO NOTHING;
    """)
    db_session.execute(query, {"msg_id": msg_id})
    db_session.commit()

def is_already_processed(db_session: Session, msg_id: str) -> bool:
    query = text("""
    SELECT 1 FROM processed_emails
    where message_id = :msg_id LIMIT 1
    """)
    result = db_session.execute(query, {"msg_id":msg_id}).fetchone()
    return result is not None

def save_email_not_process(db_session:Session, msg_id:str):
    query = text("""
    INSERT INTO not_processed_emails (message_id, created_at)
    VALUES (:msg_id, CURRENT_TIMESTAMP)
    ON CONFLICT (message_id) DO NOTHING
    """)
    db_session.execute(query, {"msg_id":msg_id})
    db_session.commit()

def get_email_not_process(db_session:Session, days :Optional[int]=1)->List[str]:
    if days is not None:
        query=text("""
            SELECT message_id from not_processed_emails
            WHERE created_at >= NOW() - (:days || ' days')::INTERVAL
        """)
        return db_session.execute(query,{"days":days}).scalars().all()
    else:
        query = text("""
            SELECT message_id from not_processed_emails
            """)
        return db_session.execute(query).scalars().all()
def delete_email_not_process(db_session:Session, msg_id:str):
    query = text("""
    DELETE FROM not_processed_emails WHERE message_id = :msg_id
    """)
    db_session.execute(query, {"msg_id":msg_id})
    db_session.commit()

def get_one_email_not_process(db_session:Session, id:str):
    
    query = text("""
        SELECT 1 from not_processed_emails
        WHERE message_id = :id
        """)
    return db_session.execute(query, {"message_id":id}).fetchone()