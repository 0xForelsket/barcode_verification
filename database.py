from sqlmodel import create_engine, Session

SQLALCHEMY_DATABASE_URI = 'sqlite:///barcode_verification.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False}
)

def get_session():
    with Session(engine) as session:
        yield session
