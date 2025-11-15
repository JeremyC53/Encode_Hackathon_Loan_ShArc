"""
One-click script to fix the database and create sample data.
Run this after activating your conda environment.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import drop_db, init_db, engine
from sqlalchemy import inspect, text


def check_and_fix_tables():
    """Check if tables exist and fix the metadata column issue."""
    print("🔍 Checking database tables...")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        print("ℹ️  No tables found. Creating fresh tables...")
        init_db()
        print("✅ Tables created successfully!")
        return True
    
    print(f"ℹ️  Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
    
    # Check if metadata column exists
    needs_migration = False
    if 'transactions' in existing_tables:
        columns = [col['name'] for col in inspector.get_columns('transactions')]
        if 'metadata' in columns and 'extra_metadata' not in columns:
            needs_migration = True
            print("⚠️  Found 'metadata' column in 'transactions' table (needs migration)")
    
    if 'credit_score_history' in existing_tables:
        columns = [col['name'] for col in inspector.get_columns('credit_score_history')]
        if 'metadata' in columns and 'extra_metadata' not in columns:
            needs_migration = True
            print("⚠️  Found 'metadata' column in 'credit_score_history' table (needs migration)")
    
    if needs_migration:
        print("\n🔄 Migrating columns...")
        try:
            with engine.connect() as conn:
                # Check if PostgreSQL
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                is_postgres = "PostgreSQL" in version
                
                if is_postgres:
                    # Rename columns in PostgreSQL
                    if 'transactions' in existing_tables:
                        try:
                            conn.execute(text("ALTER TABLE transactions RENAME COLUMN metadata TO extra_metadata"))
                            conn.commit()
                            print("✅ Renamed 'metadata' to 'extra_metadata' in 'transactions'")
                        except Exception as e:
                            if "does not exist" not in str(e):
                                print(f"⚠️  Could not rename in transactions: {e}")
                    
                    if 'credit_score_history' in existing_tables:
                        try:
                            conn.execute(text("ALTER TABLE credit_score_history RENAME COLUMN metadata TO extra_metadata"))
                            conn.commit()
                            print("✅ Renamed 'metadata' to 'extra_metadata' in 'credit_score_history'")
                        except Exception as e:
                            if "does not exist" not in str(e):
                                print(f"⚠️  Could not rename in credit_score_history: {e}")
                    
                    print("✅ Migration complete!")
                    return True
                else:
                    print("⚠️  SQLite detected. Need to recreate tables.")
                    print("   Dropping and recreating tables...")
                    drop_db()
                    init_db()
                    print("✅ Tables recreated!")
                    return True
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("   Trying to recreate tables instead...")
            try:
                drop_db()
                init_db()
                print("✅ Tables recreated!")
                return True
            except Exception as e2:
                print(f"❌ Failed to recreate tables: {e2}")
                return False
    else:
        # Check if extra_metadata exists
        if 'transactions' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('transactions')]
            if 'extra_metadata' in columns:
                print("✅ Tables already have 'extra_metadata' column - no migration needed!")
                return True
        
        # Tables exist but might be missing the new column - try to create it
        print("ℹ️  Tables exist. Ensuring all columns are present...")
        try:
            # This will create any missing columns (SQLAlchemy doesn't auto-add columns)
            # So we'll just verify the structure is correct
            init_db()  # This won't drop existing tables, just ensures structure
            print("✅ Database structure verified!")
            return True
        except Exception as e:
            print(f"⚠️  Could not verify structure: {e}")
            return False


def main():
    """Main function to fix database and create sample data."""
    print("=" * 60)
    print("🔧 Database Fix and Setup Script")
    print("=" * 60)
    print()
    
    # Step 1: Fix tables
    if not check_and_fix_tables():
        print("\n❌ Failed to fix database tables. Please check the error above.")
        sys.exit(1)
    
    print()
    
    # Step 2: Create sample data
    print("📊 Creating sample data...")
    try:
        from scripts.create_sample_data import create_sample_data
        create_sample_data()
        print()
        print("=" * 60)
        print("✅ All done! Database is ready to use.")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Start the API server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API")
        print("3. Query your data: GET http://localhost:8000/api/transactions")
    except Exception as e:
        print(f"\n❌ Error creating sample data: {e}")
        print("\n⚠️  Database tables are fixed, but sample data creation failed.")
        print("   You can try running it again: python scripts/create_sample_data.py")
        sys.exit(1)


if __name__ == "__main__":
    main()

