from sqlmodel import Session, select, SQLModel
from database import engine
from models import Job, Scan
import sys

def migrate_add_cached_counts():
    """
    Migration script to add cached count columns and populate them.
    
    This script:
    1. Creates the new columns (if not already present)
    2. Calculates correct counts for all existing jobs
    3. Updates all job records
    """
    
    print("Starting migration: Add cached counts to Job table")
    print("=" * 60)
    
    try:
        # Create all tables (will add new columns)
        # SQLModel.metadata.create_all(engine) # create_all doesn't alter existing tables
        
        from sqlalchemy import text
        with Session(engine) as session:
            print("Checking/Adding columns...")
            try:
                session.exec(text("ALTER TABLE jobs ADD COLUMN cached_pass_count INTEGER DEFAULT 0"))
                print("  Added cached_pass_count")
            except Exception as e:
                print(f"  cached_pass_count might already exist: {e}")

            try:
                session.exec(text("ALTER TABLE jobs ADD COLUMN cached_fail_count INTEGER DEFAULT 0"))
                print("  Added cached_fail_count")
            except Exception as e:
                print(f"  cached_fail_count might already exist: {e}")

            try:
                session.exec(text("ALTER TABLE jobs ADD COLUMN cached_total_scans INTEGER DEFAULT 0"))
                print("  Added cached_total_scans")
            except Exception as e:
                print(f"  cached_total_scans might already exist: {e}")
            
            session.commit()
        
        print("✓ Database schema updated")
        
        with Session(engine) as session:
            # Get all jobs
            jobs = session.exec(select(Job)).all()
            print(f"Found {len(jobs)} jobs to migrate")
            
            if not jobs:
                print("No jobs found - migration complete")
                return True
            
            # Update each job
            updated_count = 0
            for i, job in enumerate(jobs, 1):
                # Calculate actual counts from scans
                pass_count = len([s for s in job.scans if s.status == 'PASS'])
                fail_count = len([s for s in job.scans if s.status == 'FAIL'])
                total_count = len(job.scans)
                
                # Update cached values
                job.cached_pass_count = pass_count
                job.cached_fail_count = fail_count
                job.cached_total_scans = total_count
                
                session.add(job)
                updated_count += 1
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(jobs)} jobs processed")
            
            # Commit all changes
            session.commit()
            print(f"✓ Updated {updated_count} jobs")
            
            # Verify
            print("\nVerification:")
            sample_jobs = session.exec(select(Job).limit(5)).all()
            for job in sample_jobs:
                print(f"  Job {job.job_id}: "
                      f"pass={job.cached_pass_count}, "
                      f"fail={job.cached_fail_count}, "
                      f"total={job.cached_total_scans}")
            
            print("\n" + "=" * 60)
            print("Migration completed successfully!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_add_cached_counts()
    sys.exit(0 if success else 1)
