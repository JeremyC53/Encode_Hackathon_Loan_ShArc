"""
Query all transaction logs for a specific user from the database.
Outputs JSON format with fields: user_address, transaction_type, amount, currency.

Usage:
    # Using SQLAlchemy ORM (recommended)
    python -m scripts.query_user_logs 0x1234567890abcdef1234567890abcdef12345678

    # Using raw SQL
    python -m scripts.query_user_logs 0x1234567890abcdef1234567890abcdef12345678 --raw-sql

    # Save to file
    python -m scripts.query_user_logs 0x1234567890abcdef1234567890abcdef12345678 --output user_logs.json
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models import Transaction
from sqlalchemy import desc, text
from sqlalchemy.orm import Session


def query_user_logs_orm(user_address: str, db: Session) -> list[Transaction]:
    """
    Query user logs using SQLAlchemy ORM (recommended method).
    
    Args:
        user_address: Ethereum address of the user (0x...)
        db: Database session
        
    Returns:
        List of Transaction objects
    """
    # Normalize address (lowercase)
    user_address = user_address.strip().lower()
    
    # Query all transactions for this user, ordered by most recent first
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_address == user_address)
        .order_by(desc(Transaction.transaction_timestamp))
        .all()
    )
    
    return transactions


def query_user_logs_raw_sql(user_address: str, db: Session) -> list[dict]:
    """
    Query user logs using raw SQL.
    
    Args:
        user_address: Ethereum address of the user (0x...)
        db: Database session
        
    Returns:
        List of dictionaries with transaction data (only user_address, transaction_type, amount, currency)
    """
    # Normalize address (lowercase)
    user_address = user_address.strip().lower()
    
    # Raw SQL query - only select the fields we need
    sql_query = text("""
        SELECT 
            user_address,
            transaction_type,
            amount,
            currency
        FROM transactions
        WHERE LOWER(user_address) = :user_address
        ORDER BY transaction_timestamp DESC
    """)
    
    # Execute query
    result = db.execute(sql_query, {"user_address": user_address})
    
    # Convert to list of dictionaries
    transactions = []
    for row in result:
        transactions.append({
            "user_address": row.user_address,
            "transaction_type": row.transaction_type,
            "amount": float(row.amount) if row.amount else None,
            "currency": row.currency,
        })
    
    return transactions


def format_transaction(tx: Transaction) -> str:
    """Format a transaction for display."""
    lines = [
        f"  ID: {tx.id}",
        f"  Type: {tx.transaction_type}",
        f"  Amount: {tx.amount} {tx.currency}",
        f"  Status: {tx.status}",
    ]
    
    if tx.loan_id:
        lines.append(f"  Loan ID: {tx.loan_id}")
    if tx.tx_hash:
        lines.append(f"  TX Hash: {tx.tx_hash[:20]}...")
    if tx.block_number:
        lines.append(f"  Block: {tx.block_number}")
    
    lines.append(f"  Timestamp: {tx.transaction_timestamp}")
    lines.append(f"  Created: {tx.created_at}")
    
    if tx.extra_metadata:
        lines.append(f"  Metadata: {tx.extra_metadata[:50]}...")
    
    return "\n".join(lines)


def print_transactions_orm(transactions: list[Transaction]):
    """Print transactions queried via ORM."""
    if not transactions:
        print("  ⚠️  No transactions found for this user.")
        return
    
    print(f"\n📝 Found {len(transactions)} transaction(s):\n")
    print("=" * 70)
    
    for i, tx in enumerate(transactions, 1):
        print(f"\nTransaction #{i}:")
        print("-" * 70)
        print(format_transaction(tx))
    
    print("\n" + "=" * 70)


def print_transactions_raw(transactions: list[dict]):
    """Print transactions queried via raw SQL."""
    if not transactions:
        print("  ⚠️  No transactions found for this user.")
        return
    
    print(f"\n📝 Found {len(transactions)} transaction(s) (Raw SQL):\n")
    print("=" * 70)
    
    for i, tx in enumerate(transactions, 1):
        print(f"\nTransaction #{i}:")
        print("-" * 70)
        for key, value in tx.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)


def export_to_json(transactions: list[Transaction], output_file: Optional[str] = None):
    """Export transactions to JSON file with only user_address, transaction_type, amount, and currency."""
    data = []
    for tx in transactions:
        data.append({
            "user_address": tx.user_address,
            "transaction_type": tx.transaction_type,
            "amount": float(tx.amount),
            "currency": tx.currency,
        })
    
    json_str = json.dumps(data, indent=2, default=str)
    
    if output_file:
        with open(output_file, "w") as f:
            f.write(json_str)
        print(f"\n✅ Exported {len(data)} transactions to {output_file}")
    else:
        print(json_str)


def main():
    """Main function to query user logs."""
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.query_user_logs <user_address> [--raw-sql] [--output <file>]")
        print("\nExamples:")
        print("  python -m scripts.query_user_logs 0x1234...")
        print("  python -m scripts.query_user_logs 0x1234... --raw-sql")
        print("  python -m scripts.query_user_logs 0x1234... --output user_logs.json")
        print("\nNote: Output is always in JSON format with fields: user_address, transaction_type, amount, currency")
        sys.exit(1)
    
    user_address = sys.argv[1]
    use_raw_sql = "--raw-sql" in sys.argv
    
    # Get output file if specified
    output_file = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    # Validate address format
    if not user_address.startswith("0x") or len(user_address) < 10:
        print(f"❌ Error: Invalid user address format: {user_address}")
        print("   Expected format: 0x followed by hexadecimal characters")
        sys.exit(1)
    
    db = SessionLocal()
    
    try:
        if use_raw_sql:
            # Use raw SQL
            transactions = query_user_logs_raw_sql(user_address, db)
            # Output as JSON
            json_str = json.dumps(transactions, indent=2, default=str)
            if output_file:
                with open(output_file, "w") as f:
                    f.write(json_str)
                print(f"✅ Exported {len(transactions)} transactions to {output_file}")
            else:
                print(json_str)
        else:
            # Use ORM (default)
            transactions = query_user_logs_orm(user_address, db)
            # Output as JSON
            export_to_json(transactions, output_file)
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

