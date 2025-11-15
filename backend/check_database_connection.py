"""
Check which database is being used and verify connection.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, SessionLocal
from app.models import Transaction, LoanHistory
from sqlalchemy import text, inspect


def check_database():
    """Check database connection and show what's being used."""
    print("🔍 Checking database connection...")
    print()
    
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL", "sqlite:///./loan_sharc.db")
    print(f"📊 DATABASE_URL: {db_url[:50]}..." if len(db_url) > 50 else f"📊 DATABASE_URL: {db_url}")
    
    if db_url.startswith("sqlite"):
        print("⚠️  WARNING: Using SQLite (local file), NOT Supabase!")
        print("   To use Supabase, set DATABASE_URL in .env file")
    elif "supabase" in db_url.lower() or "postgres" in db_url.lower():
        print("✅ Using PostgreSQL (Supabase)")
    else:
        print("ℹ️  Using custom database connection")
    
    print()
    
    # Test connection
    try:
        with engine.connect() as conn:
            if db_url.startswith("sqlite"):
                # SQLite doesn't have version() function
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                print(f"✅ Database connected!")
                print(f"   SQLite Version: {version}")
                is_postgres = False
            else:
                # PostgreSQL
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ Database connected!")
                print(f"   Version: {version.split(',')[0]}")
                
                # Check if it's PostgreSQL
                is_postgres = "PostgreSQL" in version
                if is_postgres:
                    # Get database name
                    result = conn.execute(text("SELECT current_database()"))
                    db_name = result.fetchone()[0]
                    print(f"   Database: {db_name}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    print()
    
    # Check tables
    print("📋 Checking tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
        
        # Count records
        db = SessionLocal()
        try:
            tx_count = db.query(Transaction).count()
            loan_count = db.query(LoanHistory).count()
            
            print()
            print(f"📊 Records in database:")
            print(f"   Transactions: {tx_count}")
            print(f"   Loans: {loan_count}")
            
            if tx_count > 0:
                print()
                print("📝 Latest transactions:")
                latest = db.query(Transaction).order_by(Transaction.id.desc()).limit(3).all()
                for tx in latest:
                    print(f"   - ID {tx.id}: {tx.transaction_type} - {tx.amount} {tx.currency} (User: {tx.user_address[:10]}...)")
        finally:
            db.close()
    else:
        print("⚠️  No tables found. Run: python -m app.init_db")
    
    print()
    
    # Check .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file, "r") as f:
            content = f.read()
            if "[YOUR-PASSWORD]" in content:
                print("⚠️  WARNING: .env file still has [YOUR-PASSWORD] placeholder!")
                print("   Update it with your actual Supabase password")
    else:
        print("⚠️  .env file not found")
        print("   Create one with your DATABASE_URL")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Database Connection Check")
    print("=" * 60)
    print()
    
    check_database()
    
    print("=" * 60)

