"""
Initialize database with sample data for testing.
Run: python -m scripts.init_sample_data
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models import Transaction, LoanHistory, CreditScoreHistory


def create_sample_data():
    """Create sample transactions, loans, and credit scores."""
    print("Creating sample data...")
    
    init_db()
    db = SessionLocal()
    
    try:
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
                credit_score=650 + (i * 100),
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
                "apr_bps": 1500,
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
                "apr_bps": 1200,
            },
            {
                "loan_id": 3,
                "user_address": users[0].lower(),
                "principal": Decimal("3000.00"),
                "service_fee": Decimal("300.00"),
                "total_owed": Decimal("3300.00"),
                "amount_repaid": Decimal("3300.00"),
                "is_active": False,
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
            {"user": users[0], "type": "loan_issued", "amount": Decimal("5000.00"), "loan_id": 1, "days": 10},
            {"user": users[0], "type": "repay", "amount": Decimal("1000.00"), "loan_id": 1, "days": 40},
            {"user": users[0], "type": "repay", "amount": Decimal("1000.00"), "loan_id": 1, "days": 50},
            {"user": users[1], "type": "loan_issued", "amount": Decimal("10000.00"), "loan_id": 2, "days": 20},
            {"user": users[1], "type": "repay", "amount": Decimal("2750.00"), "loan_id": 2, "days": 45},
            {"user": users[1], "type": "repay", "amount": Decimal("2750.00"), "loan_id": 2, "days": 55},
            {"user": users[0], "type": "loan_issued", "amount": Decimal("3000.00"), "loan_id": 3, "days": 30},
            {"user": users[0], "type": "repay", "amount": Decimal("1100.00"), "loan_id": 3, "days": 50},
            {"user": users[0], "type": "repay", "amount": Decimal("1100.00"), "loan_id": 3, "days": 55},
            {"user": users[0], "type": "repay", "amount": Decimal("1100.00"), "loan_id": 3, "days": 60},
        ]
        
        for i, tx_data in enumerate(transactions_data):
            tx = Transaction(
                user_address=tx_data["user"].lower(),
                transaction_type=tx_data["type"],
                amount=tx_data["amount"],
                currency="USDC",
                loan_id=tx_data["loan_id"],
                tx_hash=f"0x{str(i+1) * 64}",
                block_number=1000 + i * 100,
                transaction_timestamp=base_time + timedelta(days=tx_data["days"]),
                status="confirmed",
            )
            db.add(tx)
        
        db.commit()
        print(f"\n✅ Sample data created: {len(users)} users, {len(loans_data)} loans, {len(transactions_data)} transactions")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()

