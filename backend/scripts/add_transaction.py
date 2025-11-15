"""
Helper script to manually add a transaction to the database.
Useful for testing or manually syncing transactions.
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Transaction


def add_transaction(
    user_address: str,
    transaction_type: str,
    amount: float,
    loan_id: int | None = None,
    tx_hash: str | None = None,
    block_number: int | None = None,
    status: str = "confirmed",
):
    """Add a transaction to the database."""
    db = SessionLocal()
    
    try:
        transaction = Transaction(
            user_address=user_address.lower(),
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            currency="USDC",
            loan_id=loan_id,
            tx_hash=tx_hash,
            block_number=block_number,
            transaction_timestamp=datetime.now(timezone.utc),
            status=status,
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        print(f"✅ Transaction added:")
        print(f"   ID: {transaction.id}")
        print(f"   User: {transaction.user_address}")
        print(f"   Type: {transaction.transaction_type}")
        print(f"   Amount: {transaction.amount} {transaction.currency}")
        if loan_id:
            print(f"   Loan ID: {loan_id}")
        if tx_hash:
            print(f"   TX Hash: {tx_hash}")
        
        return transaction
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding transaction: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a transaction to the database")
    parser.add_argument("--user", required=True, help="User wallet address")
    parser.add_argument("--type", required=True, choices=["borrow", "repay", "loan_issued"], help="Transaction type")
    parser.add_argument("--amount", type=float, required=True, help="Amount in USDC")
    parser.add_argument("--loan-id", type=int, help="Loan ID (optional)")
    parser.add_argument("--tx-hash", help="Transaction hash (optional)")
    parser.add_argument("--block", type=int, help="Block number (optional)")
    parser.add_argument("--status", default="confirmed", help="Transaction status")
    
    args = parser.parse_args()
    
    add_transaction(
        user_address=args.user,
        transaction_type=args.type,
        amount=args.amount,
        loan_id=args.loan_id,
        tx_hash=args.tx_hash,
        block_number=args.block,
        status=args.status,
    )

