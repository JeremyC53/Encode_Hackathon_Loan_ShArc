"""
Simulate a new transaction and store it in Supabase.
This creates a realistic loan transaction and stores it in the database.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models import Transaction, LoanHistory


def simulate_new_transaction():
    """Simulate a new loan transaction and store it in the database."""
    print("🔄 Simulating new transaction...")
    
    # Ensure database is initialized
    init_db()
    
    db = SessionLocal()
    
    try:
        # Simulate a new user borrowing money
        new_user = "0x9876543210fedcba9876543210fedcba98765432"
        loan_amount = Decimal("7500.00")
        service_fee = Decimal("750.00")  # 10% service fee
        total_owed = loan_amount + service_fee
        
        # Get the next loan ID (find max existing loan_id)
        max_loan = db.query(LoanHistory).order_by(LoanHistory.loan_id.desc()).first()
        next_loan_id = (max_loan.loan_id + 1) if max_loan else 1
        
        print(f"\n📝 Creating new loan transaction:")
        print(f"   User: {new_user}")
        print(f"   Loan ID: {next_loan_id}")
        print(f"   Amount: {loan_amount} USDC")
        print(f"   Service Fee: {service_fee} USDC")
        print(f"   Total Owed: {total_owed} USDC")
        
        # Create loan history record
        loan = LoanHistory(
            loan_id=next_loan_id,
            user_address=new_user.lower(),
            principal=loan_amount,
            service_fee=service_fee,
            total_owed=total_owed,
            amount_repaid=Decimal("0"),
            is_active=True,
            loan_timestamp=datetime.now(timezone.utc),
            tx_hash=f"0x{'b' * 64}",  # Simulated transaction hash
            credit_score_at_issuance=720,
            apr_bps=1300,  # 13% APR
        )
        db.add(loan)
        
        # Create transaction record for loan issuance
        loan_transaction = Transaction(
            user_address=new_user.lower(),
            transaction_type="loan_issued",
            amount=loan_amount,
            currency="USDC",
            loan_id=next_loan_id,
            tx_hash=f"0x{'b' * 64}",
            block_number=5000,  # Simulated block number
            transaction_timestamp=datetime.now(timezone.utc),
            status="confirmed",
            extra_metadata=f'{{"serviceFee": {service_fee}, "totalOwed": {total_owed}, "creditScore": 720}}',
        )
        db.add(loan_transaction)
        
        # Simulate a repayment transaction (30 days later)
        repayment_amount = Decimal("2750.00")  # First installment
        repayment_tx = Transaction(
            user_address=new_user.lower(),
            transaction_type="repay",
            amount=repayment_amount,
            currency="USDC",
            loan_id=next_loan_id,
            tx_hash=f"0x{'c' * 64}",
            block_number=5100,
            transaction_timestamp=datetime.now(timezone.utc) + timedelta(days=30),
            status="confirmed",
            extra_metadata=f'{{"remainingBalance": {total_owed - repayment_amount}}}',
        )
        db.add(repayment_tx)
        
        # Update loan repayment amount
        loan.amount_repaid = repayment_amount
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Transaction created successfully!")
        print(f"   Transaction ID: {loan_transaction.id}")
        print(f"   Repayment Transaction ID: {repayment_tx.id}")
        print(f"\n📊 Summary:")
        print(f"   - Loan #{next_loan_id} issued: {loan_amount} USDC")
        print(f"   - First repayment: {repayment_amount} USDC")
        print(f"   - Remaining balance: {total_owed - repayment_amount} USDC")
        print(f"\n🔍 You can now:")
        print(f"   1. Check Supabase dashboard: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
        print(f"   2. Query via API: GET http://localhost:8000/api/transactions")
        print(f"   3. View loan: GET http://localhost:8000/api/loans/{next_loan_id}")
        
        return loan_transaction.id, repayment_tx.id
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating transaction: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def verify_in_database():
    """Verify the transaction was stored correctly."""
    print("\n🔍 Verifying transaction in database...")
    
    db = SessionLocal()
    
    try:
        # Get the latest transaction
        latest_tx = db.query(Transaction).order_by(Transaction.id.desc()).first()
        
        if latest_tx:
            print(f"✅ Found latest transaction:")
            print(f"   ID: {latest_tx.id}")
            print(f"   User: {latest_tx.user_address}")
            print(f"   Type: {latest_tx.transaction_type}")
            print(f"   Amount: {latest_tx.amount} {latest_tx.currency}")
            print(f"   Loan ID: {latest_tx.loan_id}")
            print(f"   Status: {latest_tx.status}")
            print(f"   Created: {latest_tx.created_at}")
            
            # Count total transactions
            total_txs = db.query(Transaction).count()
            print(f"\n📊 Total transactions in database: {total_txs}")
            
            # Count total loans
            total_loans = db.query(LoanHistory).count()
            print(f"📊 Total loans in database: {total_loans}")
            
            return True
        else:
            print("❌ No transactions found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 Simulating New Transaction")
    print("=" * 60)
    print()
    
    # Create the transaction
    tx_id, repay_id = simulate_new_transaction()
    
    # Verify it was stored
    verify_in_database()
    
    print("\n" + "=" * 60)
    print("✅ Done! Check your Supabase dashboard to see the new data.")
    print("=" * 60)

