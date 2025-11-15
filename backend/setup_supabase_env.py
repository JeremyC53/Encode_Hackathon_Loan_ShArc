"""
Interactive script to set up Supabase connection in .env file.
"""
from __future__ import annotations

import os
from pathlib import Path


def setup_supabase_env():
    """Set up .env file with Supabase connection string."""
    print("=" * 60)
    print("🔧 Supabase Connection Setup")
    print("=" * 60)
    print()
    
    env_file = Path(__file__).parent / ".env"
    
    # Check if .env exists
    if env_file.exists():
        print("📄 Found existing .env file")
        with open(env_file, "r") as f:
            content = f.read()
            if "DATABASE_URL" in content and "supabase" in content.lower():
                print("✅ .env already has Supabase connection string")
                print()
                print("Current DATABASE_URL:")
                for line in content.split("\n"):
                    if "DATABASE_URL" in line and not line.strip().startswith("#"):
                        # Hide password
                        if ":" in line and "@" in line:
                            parts = line.split("@")
                            if len(parts) == 2:
                                user_pass = parts[0].split(":")[-1]
                                if user_pass:
                                    masked = line.replace(user_pass, "***")
                                    print(f"   {masked}")
                                else:
                                    print(f"   {line}")
                            else:
                                print(f"   {line}")
                        else:
                            print(f"   {line}")
                
                update = input("\nUpdate it? (y/n): ").strip().lower()
                if update != "y":
                    print("Keeping existing .env file")
                    return
    else:
        print("📄 Creating new .env file")
    
    print()
    print("To get your Supabase connection string:")
    print("1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
    print("2. Click 'Settings' (gear icon) → 'Database'")
    print("3. Find 'Connection string' → 'URI'")
    print("4. Copy the connection string")
    print()
    print("It should look like:")
    print("   postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres")
    print()
    
    # Get connection string
    connection_string = input("Paste your Supabase connection string (or press Enter to use template): ").strip()
    
    if not connection_string:
        # Use template
        password = input("Enter your Supabase database password: ").strip()
        if not password:
            print("❌ Password required!")
            return
        
        connection_string = f"postgresql://postgres.jmwhsuqhzdurrbynxuwd:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    # Replace [YOUR-PASSWORD] if present
    if "[YOUR-PASSWORD]" in connection_string:
        password = input("Enter your Supabase database password: ").strip()
        connection_string = connection_string.replace("[YOUR-PASSWORD]", password)
    
    # Write .env file
    env_content = f"""# Database Configuration
# Supabase PostgreSQL connection
DATABASE_URL={connection_string}

# Alternative: Use SQLite for local development (comment out line above, uncomment below)
# DATABASE_URL=sqlite:///./loan_sharc.db

# Blockchain Configuration (optional)
# CREDIT_LOAN_CONTRACT=0x0000000000000000000000000000000000000000
# RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print()
    print("✅ .env file created/updated!")
    print()
    print("⚠️  IMPORTANT: Restart your server for changes to take effect!")
    print()
    print("Next steps:")
    print("1. Stop your server (Ctrl+C)")
    print("2. Restart: uvicorn app.main:app --reload")
    print("3. Run: python check_database_connection.py (should show Supabase)")
    print("4. Run: python scripts/simulate_transaction.py (to add data to Supabase)")


if __name__ == "__main__":
    setup_supabase_env()

