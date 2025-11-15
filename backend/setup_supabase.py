"""
Setup script for connecting to Supabase PostgreSQL database.
This script helps you get your connection string and test the connection.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

def get_supabase_connection_string() -> str:
    """
    Guide user through getting Supabase connection string.
    """
    print("=" * 60)
    print("Supabase Database Setup")
    print("=" * 60)
    print("\nTo get your Supabase connection string:")
    print("1. Go to your Supabase project: https://supabase.com/dashboard")
    print("2. Click on 'Project Settings' (gear icon)")
    print("3. Go to 'Database' section")
    print("4. Find 'Connection string' → 'URI'")
    print("5. Copy the connection string (it looks like:)")
    print("   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres")
    print("\n" + "-" * 60)
    
    # Check if already set in environment
    existing_url = os.getenv("DATABASE_URL")
    if existing_url and not existing_url.startswith("sqlite"):
        print(f"\n✅ Found existing DATABASE_URL: {existing_url[:50]}...")
        use_existing = input("Use this? (y/n): ").strip().lower()
        if use_existing == 'y':
            return existing_url
    
    # Get connection string from user
    print("\nEnter your Supabase connection string:")
    print("(Or press Enter to use SQLite for local development)")
    connection_string = input("> ").strip()
    
    if not connection_string:
        print("\n⚠️  No connection string provided. Using SQLite for local development.")
        return "sqlite:///./loan_sharc.db"
    
    # Replace [YOUR-PASSWORD] if user entered placeholder
    if "[YOUR-PASSWORD]" in connection_string:
        password = input("\nEnter your database password: ").strip()
        connection_string = connection_string.replace("[YOUR-PASSWORD]", password)
    
    return connection_string


def save_to_env_file(connection_string: str) -> None:
    """Save connection string to .env file."""
    env_file = Path(__file__).parent / ".env"
    
    # Read existing .env if it exists
    env_vars = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update DATABASE_URL
    env_vars["DATABASE_URL"] = connection_string
    
    # Write back to .env
    with open(env_file, "w") as f:
        f.write("# Database Configuration\n")
        f.write(f"DATABASE_URL={connection_string}\n")
        f.write("\n# Add other environment variables below\n")
        for key, value in env_vars.items():
            if key != "DATABASE_URL":
                f.write(f"{key}={value}\n")
    
    print(f"\n✅ Saved DATABASE_URL to {env_file}")


def test_connection(connection_string: str) -> bool:
    """Test database connection."""
    print("\n" + "-" * 60)
    print("Testing database connection...")
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(connection_string, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   Database: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nCommon issues:")
        print("1. Check your password is correct")
        print("2. Verify the connection string format")
        print("3. Make sure your IP is allowed in Supabase (Settings → Database → Connection Pooling)")
        return False


def main():
    """Main setup function."""
    print("\n🚀 Setting up Supabase connection...\n")
    
    # Get connection string
    connection_string = get_supabase_connection_string()
    
    # Test connection
    if not connection_string.startswith("sqlite"):
        if not test_connection(connection_string):
            print("\n❌ Setup incomplete. Please fix the connection and try again.")
            sys.exit(1)
    
    # Save to .env file
    save_to_env_file(connection_string)
    
    # Set environment variable for current session
    os.environ["DATABASE_URL"] = connection_string
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Initialize database: python -m app.init_db")
    print("2. Create sample data: python scripts/create_sample_data.py")
    print("3. Start the API: uvicorn app.main:app --reload")
    print("\nYour connection string is saved in .env file")
    print("The app will automatically use it when you start the server.")


if __name__ == "__main__":
    main()

