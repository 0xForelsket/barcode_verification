from sqlmodel import create_engine, Session

SQLALCHEMY_DATABASE_URI = 'sqlite:///barcode_verification.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False}
)

# Enable WAL mode and performance optimizations for SQLite
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

def get_session():
    with Session(engine) as session:
        yield session

def get_session_direct() -> Session:
    """Non-generator session for internal use (lifespan, etc.)"""
    return Session(engine)
