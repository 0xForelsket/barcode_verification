import sqlite3
import os

DB_FILE = "barcode_verification.db"


def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Skipping migration.")
        return

    print(f"Migrating {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Add is_locked column
        print("Adding is_locked column to jobs table...")
        cursor.execute("ALTER TABLE jobs ADD COLUMN is_locked BOOLEAN DEFAULT 0")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("Column is_locked already exists. Skipping.")
        else:
            print(f"Error adding column: {e}")
            # Don't raise, just continue (idempotency)

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
