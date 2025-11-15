"""
Create sample transaction and loan data for testing.
This script populates the database with realistic sample data.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models import Transaction, LoanHistory, CreditScoreHistory


def create_sample_data():
    """Create sample transactions, loans, and credit scores."""
    print("Creating sample data...")
    
    # Initialize database if needed
    init_db()
    
    db = SessionLocal()
    
    try:
        # Sample user addresses
        users = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x9876543210fedcba9876543210fedcba98765432",
        ]
        
        # Create credit scores
        print("  Creating credit scores...")
        for i, user in enumerate(users):
            score = CreditScoreHistory(
                user_address=user.lower(),
                credit_score=650 + (i * 100),  # 650, 750, 850
                source="freelance_scorer",
                score_timestamp=datetime.now(timezone.utc) - timedelta(days=30),
                extra_metadata='{"platforms": 3, "totalEarned": 25000}'
            )
            db.add(score)
        
        # Create loans
        print("  Creating loans...")
        loans_data = [
            {
                "loan_id": 1,
                "user_address": users[0].lower(),
                "principal": Decimal("5000.00"),
                "service_fee": Decimal("500.00"),
                "total_owed": Decimal("5500.00"),
                "amount_repaid": Decimal("2000.00"),
                "is_active": True,
                "credit_score_at_issuance": 650,
                "apr_bps": 1500,  # 15%
            },
            {
                "loan_id": 2,
                "user_address": users[1].lower(),
                "principal": Decimal("10000.00"),
                "service_fee": Decimal("1000.00"),
                "total_owed": Decimal("11000.00"),
                "amount_repaid": Decimal("5500.00"),
                "is_active": True,
                "credit_score_at_issuance": 750,
                "apr_bps": 1200,  # 12%
            },
            {
                "loan_id": 3,
                "user_address": users[0].lower(),
                "principal": Decimal("3000.00"),
                "service_fee": Decimal("300.00"),
                "total_owed": Decimal("3300.00"),
                "amount_repaid": Decimal("3300.00"),
                "is_active": False,  # Fully repaid
                "credit_score_at_issuance": 650,
                "apr_bps": 1500,
            },
        ]
        
        base_time = datetime.now(timezone.utc) - timedelta(days=60)
        
        for loan_data in loans_data:
            loan = LoanHistory(
                loan_id=loan_data["loan_id"],
                user_address=loan_data["user_address"],
                principal=loan_data["principal"],
                service_fee=loan_data["service_fee"],
                total_owed=loan_data["total_owed"],
                amount_repaid=loan_data["amount_repaid"],
                is_active=loan_data["is_active"],
                loan_timestamp=base_time + timedelta(days=loan_data["loan_id"] * 10),
                tx_hash=f"0x{'a' * 64}",
                credit_score_at_issuance=loan_data["credit_score_at_issuance"],
                apr_bps=loan_data["apr_bps"],
            )
            db.add(loan)
        
        # Create transactions
        print("  Creating transactions...")
        transactions_data = [
            # Loan 1 transactions
            {
                "user_address": users[0].lower(),
                "transaction_type": "loan_issued",
                "amount": Decimal("5000.00"),
                "loan_id": 1,
                "tx_hash": "0x1111111111111111111111111111111111111111111111111111111111111111",
                "block_number": 1000,
                "transaction_timestamp": base_time + timedelta(days=10),
                "status": "confirmed",
            },
            {
                "user_address": users[0].lower(),
                "transaction_type": "repay",
                "amount": Decimal("1000.00"),
                "loan_id": 1,
                "tx_hash": "0x2222222222222222222222222222222222222222222222222222222222222222",
                "block_number": 1100,
                "transaction_timestamp": base_time + timedelta(days=40),
                "status": "confirmed",
            },
            {
                "user_address": users[0].lower(),
                "transaction_type": "repay",
                "amount": Decimal("1000.00"),
                "loan_id": 1,
                "tx_hash": "0x3333333333333333333333333333333333333333333333333333333333333333",
                "block_number": 1200,
                "transaction_timestamp": base_time + timedelta(days=50),
                "status": "confirmed",
            },
            # Loan 2 transactions
            {
                "user_address": users[1].lower(),
                "transaction_type": "loan_issued",
                "amount": Decimal("10000.00"),
                "loan_id": 2,
                "tx_hash": "0x4444444444444444444444444444444444444444444444444444444444444444",
                "block_number": 2000,
                "transaction_timestamp": base_time + timedelta(days=20),
                "status": "confirmed",
            },
            {
                "user_address": users[1].lower(),
                "transaction_type": "repay",
                "amount": Decimal("2750.00"),
                "loan_id": 2,
                "tx_hash": "0x5555555555555555555555555555555555555555555555555555555555555555",
                "block_number": 2100,
                "transaction_timestamp": base_time + timedelta(days=45),
                "status": "confirmed",
            },
            {
                "user_address": users[1].lower(),
                "transaction_type": "repay",
                "amount": Decimal("2750.00"),
                "loan_id": 2,
                "tx_hash": "0x6666666666666666666666666666666666666666666666666666666666666666",
                "block_number": 2200,
                "transaction_timestamp": base_time + timedelta(days=55),
                "status": "confirmed",
            },
            # Loan 3 transactions (fully repaid)
            {
                "user_address": users[0].lower(),
                "transaction_type": "loan_issued",
                "amount": Decimal("3000.00"),
                "loan_id": 3,
                "tx_hash": "0x7777777777777777777777777777777777777777777777777777777777777777",
                "block_number": 3000,
                "transaction_timestamp": base_time + timedelta(days=30),
                "status": "confirmed",
            },
            {
                "user_address": users[0].lower(),
                "transaction_type": "repay",
                "amount": Decimal("1100.00"),
                "loan_id": 3,
                "tx_hash": "0x8888888888888888888888888888888888888888888888888888888888888888",
                "block_number": 3100,
                "transaction_timestamp": base_time + timedelta(days=50),
                "status": "confirmed",
            },
            {
                "user_address": users[0].lower(),
                "transaction_type": "repay",
                "amount": Decimal("1100.00"),
                "loan_id": 3,
                "tx_hash": "0x9999999999999999999999999999999999999999999999999999999999999999",
                "block_number": 3200,
                "transaction_timestamp": base_time + timedelta(days=55),
                "status": "confirmed",
            },
            {
                "user_address": users[0].lower(),
                "transaction_type": "repay",
                "amount": Decimal("1100.00"),
                "loan_id": 3,
                "tx_hash": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "block_number": 3300,
                "transaction_timestamp": base_time + timedelta(days=60),
                "status": "confirmed",
            },
        ]
        
        for tx_data in transactions_data:
            tx = Transaction(
                user_address=tx_data["user_address"],
                transaction_type=tx_data["transaction_type"],
                amount=tx_data["amount"],
                currency="USDC",
                loan_id=tx_data.get("loan_id"),
                tx_hash=tx_data.get("tx_hash"),
                block_number=tx_data.get("block_number"),
                transaction_timestamp=tx_data["transaction_timestamp"],
                status=tx_data["status"],
            )
            db.add(tx)
        
        # Commit all changes
        db.commit()
        
        print("\n✅ Sample data created successfully!")
        print(f"\nCreated:")
        print(f"  - {len(users)} credit scores")
        print(f"  - {len(loans_data)} loans")
        print(f"  - {len(transactions_data)} transactions")
        print(f"\nYou can now query the data using the API endpoints.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()

