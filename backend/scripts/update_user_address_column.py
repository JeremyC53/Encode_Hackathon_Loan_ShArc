"""
Update user_address column length from 42 to 66 in all tables.
Run this script to fix the database schema after updating the model.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.database import engine
from sqlalchemy import text

def update_user_address_columns():
    """Update user_address column length in all relevant tables."""
    
    print("Updating user_address column length from 42 to 66...")
    
    tables_to_update = [
        "transactions",
        "loan_history",
        "credit_score_history",
    ]
    
    try:
        with engine.connect() as connection:
            # Check database type
            db_type = engine.url.get_backend_name()
            
            if db_type == "postgresql":
                # PostgreSQL: Use ALTER COLUMN
                for table in tables_to_update:
                    try:
                        query = text(
                            f'ALTER TABLE {table} '
                            f'ALTER COLUMN user_address TYPE VARCHAR(66)'
                        )
                        connection.execute(query)
                        connection.commit()
                        print(f"✅ Updated {table}.user_address to VARCHAR(66)")
                    except Exception as e:
                        print(f"⚠️  Could not update {table}.user_address: {e}")
                        # Might not exist yet, that's okay
                        connection.rollback()
            
            elif db_type == "sqlite":
                # SQLite: Need to recreate table (SQLite limitation)
                print("⚠️  SQLite doesn't support ALTER COLUMN easily.")
                print("   If you get errors, you may need to recreate the database:")
                print("   python -m app.init_db  # This will recreate all tables")
            
            else:
                print(f"⚠️  Unknown database type: {db_type}")
                print("   You may need to update the column manually")
        
        print("\n✅ Update complete!")
        print("   Note: If using SQLite and you still get errors,")
        print("   run: python -m app.init_db")
        
    except Exception as e:
        print(f"❌ Error updating columns: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_user_address_columns()

