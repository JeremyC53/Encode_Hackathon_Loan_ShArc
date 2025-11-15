"""
Quick script to create .env file for Supabase connection.
"""
from pathlib import Path

def create_env_file():
    """Create .env file with Supabase connection string."""
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    print("Creating .env file...")
    print("Enter your Supabase database password:")
    print("(Get it from: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd → Settings → Database)")
    
    password = input("Password: ").strip()
    
    if not password:
        print("❌ Password required!")
        return
    
    content = f"""# Database Configuration
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Blockchain Configuration (optional)
# CREDIT_LOAN_CONTRACT=0x0000000000000000000000000000000000000000
# RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
"""
    
    with open(env_file, "w") as f:
        f.write(content)
    
    print(f"✅ Created .env file at {env_file}")

if __name__ == "__main__":
    create_env_file()

