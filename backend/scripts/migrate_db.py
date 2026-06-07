"""
Database migration script — adds backup_codes column to users table.

Run once after pulling the latest code:
  python -m scripts.migrate_db
"""
from sqlalchemy import text
from app.core.database import engine

def migrate():
    with engine.connect() as conn:
        # Check if backup_codes column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='backup_codes'
        """))

        if result.fetchone() is None:
            print("Adding backup_codes column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN backup_codes JSON"))
            conn.commit()
            print("✓ Migration complete: backup_codes column added")
        else:
            print("✓ No migration needed: backup_codes column already exists")

if __name__ == "__main__":
    migrate()
