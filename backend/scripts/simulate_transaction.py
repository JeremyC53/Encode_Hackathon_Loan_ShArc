"""
Simulate a transaction and verify it's stored in Supabase.
Run: python -m scripts.simulate_transaction
"""
from __future__ import annotations

import sys
import requests
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Transaction, LoanHistory
from decimal import Decimal


def simulate_via_api():
    """Simulate transaction via API (requires server to be running)."""
    print("🔄 Simulating transaction via API...")
    print("   (Make sure backend server is running: uvicorn app.main:app --reload)\n")
    
    BASE_URL = "http://localhost:8000/api"
    
    # Simulate a new loan issuance
    new_user = "0x9876543210fedcba9876543210fedcba98765432"
    loan_amount = 7500.0
    service_fee = 750.0
    total_owed = loan_amount + service_fee
    loan_id = 4
    
    transaction_data = {
        "user_address": new_user,
        "transaction_type": "loan_issued",
        "amount": loan_amount,
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": f"0x{'b' * 64}",
        "block_number": 5000,
        "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed",
        "extra_metadata": json.dumps({
            "serviceFee": service_fee,
            "totalOwed": total_owed,
            "creditScore": 720
        })
    }
    
    try:
        print(f"📤 Creating loan transaction:")
        print(f"   User: {new_user}")
        print(f"   Amount: {loan_amount} USDC")
        print(f"   Loan ID: {loan_id}")
        
        response = requests.post(f"{BASE_URL}/transactions", json=transaction_data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"\n✅ Transaction created successfully!")
            print(f"   Transaction ID: {result['id']}")
            print(f"   Status: {result['status']}")
            print(f"   Created at: {result['created_at']}")
            
            # Also create a repayment
            print(f"\n📤 Creating repayment transaction...")
            repayment_data = {
                "user_address": new_user,
                "transaction_type": "repay",
                "amount": 2750.0,
                "currency": "USDC",
                "loan_id": loan_id,
                "tx_hash": f"0x{'c' * 64}",
                "block_number": 5100,
                "transaction_timestamp": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "status": "confirmed",
                "extra_metadata": json.dumps({"remainingBalance": total_owed - 2750.0})
            }
            
            response2 = requests.post(f"{BASE_URL}/transactions", json=repayment_data)
            if response2.status_code == 201:
                result2 = response2.json()
                print(f"✅ Repayment transaction created!")
                print(f"   Transaction ID: {result2['id']}")
                print(f"   Amount: {result2['amount']} USDC")
            
            print(f"\n" + "="*60)
            print("✅ Transactions created! Check Supabase dashboard:")
            print("="*60)
            print("1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
            print("2. Click 'Table Editor' in sidebar")
            print("3. Click 'transactions' table")
            print("4. You should see the new transactions!")
            print(f"\nOr query via API: GET {BASE_URL}/transactions")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server.")
        print("   Start the server first: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def simulate_via_database():
    """Simulate transaction directly in database (no server needed)."""
    print("🔄 Simulating transaction directly in database...\n")
    
    from app.database import init_db
    
    init_db()
    db = SessionLocal()
    
    try:
        # Simulate a new loan
        new_user = "0x9876543210fedcba9876543210fedcba98765432"
        loan_amount = Decimal("7500.00")
        service_fee = Decimal("750.00")
        total_owed = loan_amount + service_fee
        
        # Get next loan ID
        max_loan = db.query(LoanHistory).order_by(LoanHistory.loan_id.desc()).first()
        next_loan_id = (max_loan.loan_id + 1) if max_loan else 1
        
        print(f"📝 Creating transaction:")
        print(f"   User: {new_user}")
        print(f"   Loan ID: {next_loan_id}")
        print(f"   Amount: {loan_amount} USDC")
        
        # Create loan history
        loan = LoanHistory(
            loan_id=next_loan_id,
            user_address=new_user.lower(),
            principal=loan_amount,
            service_fee=service_fee,
            total_owed=total_owed,
            amount_repaid=Decimal("0"),
            is_active=True,
            loan_timestamp=datetime.now(timezone.utc),
            tx_hash=f"0x{'b' * 64}",
            credit_score_at_issuance=720,
            apr_bps=1300,
        )
        db.add(loan)
        
        # Create transaction
        transaction = Transaction(
            user_address=new_user.lower(),
            transaction_type="loan_issued",
            amount=loan_amount,
            currency="USDC",
            loan_id=next_loan_id,
            tx_hash=f"0x{'b' * 64}",
            block_number=5000,
            transaction_timestamp=datetime.now(timezone.utc),
            status="confirmed",
            extra_metadata=f'{{"serviceFee": {service_fee}, "totalOwed": {total_owed}}}',
        )
        db.add(transaction)
        
        # Create repayment
        repayment = Transaction(
            user_address=new_user.lower(),
            transaction_type="repay",
            amount=Decimal("2750.00"),
            currency="USDC",
            loan_id=next_loan_id,
            tx_hash=f"0x{'c' * 64}",
            block_number=5100,
            transaction_timestamp=datetime.now(timezone.utc) + timedelta(days=30),
            status="confirmed",
            extra_metadata='{"remainingBalance": 5500.0}',
        )
        db.add(repayment)
        
        loan.amount_repaid = Decimal("2750.00")
        
        db.commit()
        
        print(f"\n✅ Transactions created successfully!")
        print(f"   Transaction IDs: {transaction.id}, {repayment.id}")
        print(f"   Loan ID: {next_loan_id}")
        
        # Verify
        tx_count = db.query(Transaction).count()
        loan_count = db.query(LoanHistory).count()
        
        print(f"\n📊 Database now has:")
        print(f"   Total transactions: {tx_count}")
        print(f"   Total loans: {loan_count}")
        
        print(f"\n" + "="*60)
        print("✅ Check Supabase dashboard:")
        print("="*60)
        print("1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
        print("2. Click 'Table Editor' in sidebar")
        print("3. Click 'transactions' table")
        print("4. Look for transactions with user: " + new_user[:20] + "...")
        print("5. Or sort by 'created_at' DESC to see newest first")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate a transaction")
    parser.add_argument("--api", action="store_true", help="Use API endpoint (requires server running)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 Simulate Transaction")
    print("=" * 60)
    print()
    
    if args.api:
        success = simulate_via_api()
    else:
        print("Using direct database method (no server needed)...\n")
        success = simulate_via_database()
    
    if success:
        print("\n" + "="*60)
        print("✅ Done! Transaction simulated successfully.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Failed to simulate transaction.")
        print("="*60)

