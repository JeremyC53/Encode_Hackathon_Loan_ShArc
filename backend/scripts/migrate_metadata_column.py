"""
Migration script to rename 'metadata' column to 'extra_metadata'.
Run this if you already have tables created with the old column name.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, SessionLocal


def migrate_metadata_column():
    """Rename metadata column to extra_metadata in existing tables."""
    print("🔄 Migrating 'metadata' column to 'extra_metadata'...")
    
    db = SessionLocal()
    
    try:
        # Check if we're using PostgreSQL
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            is_postgres = "PostgreSQL" in version
            
            if is_postgres:
                print("✅ Detected PostgreSQL database")
                
                # Rename column in transactions table
                try:
                    conn.execute(text("ALTER TABLE transactions RENAME COLUMN metadata TO extra_metadata"))
                    conn.commit()
                    print("✅ Renamed 'metadata' to 'extra_metadata' in 'transactions' table")
                except Exception as e:
                    if "does not exist" in str(e) or "column" in str(e).lower():
                        print("ℹ️  'metadata' column doesn't exist in 'transactions' (might already be migrated)")
                    else:
                        raise
                
                # Rename column in credit_score_history table
                try:
                    conn.execute(text("ALTER TABLE credit_score_history RENAME COLUMN metadata TO extra_metadata"))
                    conn.commit()
                    print("✅ Renamed 'metadata' to 'extra_metadata' in 'credit_score_history' table")
                except Exception as e:
                    if "does not exist" in str(e) or "column" in str(e).lower():
                        print("ℹ️  'metadata' column doesn't exist in 'credit_score_history' (might already be migrated)")
                    else:
                        raise
                
            else:
                print("ℹ️  Detected SQLite database")
                print("⚠️  SQLite doesn't support column renaming easily.")
                print("   Recommendation: Drop and recreate tables:")
                print("   python -m app.init_db --drop")
                print("   python -m app.init_db")
                return
        
        print("\n✅ Migration complete!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_metadata_column()

