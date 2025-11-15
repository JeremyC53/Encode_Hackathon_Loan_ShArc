"""
Check transactions in Supabase database.
Run: python -m scripts.check_supabase
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Transaction, LoanHistory
from sqlalchemy import desc


def check_transactions():
    """Check transactions in the database."""
    print("=" * 60)
    print("🔍 Checking Supabase Database")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    
    try:
        # Count transactions
        tx_count = db.query(Transaction).count()
        loan_count = db.query(LoanHistory).count()
        
        print(f"📊 Database Statistics:")
        print(f"   Total Transactions: {tx_count}")
        print(f"   Total Loans: {loan_count}")
        print()
        
        if tx_count == 0:
            print("⚠️  No transactions found in database.")
            print("   Run: python -m scripts.simulate_transaction")
            return
        
        # Show latest transactions
        print("📝 Latest 5 Transactions:")
        print("-" * 60)
        latest_txs = db.query(Transaction).order_by(desc(Transaction.created_at)).limit(5).all()
        
        for tx in latest_txs:
            print(f"ID: {tx.id}")
            print(f"  User: {tx.user_address[:20]}...")
            print(f"  Type: {tx.transaction_type}")
            print(f"  Amount: {tx.amount} {tx.currency}")
            if tx.loan_id:
                print(f"  Loan ID: {tx.loan_id}")
            print(f"  Status: {tx.status}")
            print(f"  Created: {tx.created_at}")
            print()
        
        # Show active loans
        active_loans = db.query(LoanHistory).filter(LoanHistory.is_active == True).count()
        print(f"💰 Active Loans: {active_loans}")
        
        if active_loans > 0:
            print("\n📋 Active Loans:")
            print("-" * 60)
            loans = db.query(LoanHistory).filter(LoanHistory.is_active == True).all()
            for loan in loans:
                remaining = loan.total_owed - loan.amount_repaid
                print(f"Loan #{loan.loan_id}:")
                print(f"  User: {loan.user_address[:20]}...")
                print(f"  Principal: {loan.principal} USDC")
                print(f"  Repaid: {loan.amount_repaid} / {loan.total_owed} USDC")
                print(f"  Remaining: {remaining} USDC")
                print()
        
        print("=" * 60)
        print("✅ To view in Supabase dashboard:")
        print("=" * 60)
        print("1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
        print("2. Click 'Table Editor' in sidebar")
        print("3. Click 'transactions' table to see all transactions")
        print("4. Click 'loan_history' table to see all loans")
        print()
        print("💡 Tip: Sort by 'created_at' DESC to see newest first")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_transactions()

