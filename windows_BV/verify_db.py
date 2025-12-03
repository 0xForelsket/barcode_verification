from sqlmodel import Session, select
from database import engine
from models import Job

def verify_db():
    try:
        with Session(engine) as session:
            # Try to select the new columns
            stmt = select(Job.cached_pass_count).limit(1)
            session.exec(stmt)
            print("SUCCESS: cached_pass_count column exists and is accessible.")
            return True
    except Exception as e:
        print(f"FAILURE: {e}")
        return False

if __name__ == "__main__":
    verify_db()
