"""
Blockchain event listener and sync service.
This script listens to blockchain events and automatically stores transactions in the database.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web3 import Web3
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Transaction, LoanHistory


# Contract addresses (update these with your deployed contract addresses)
CREDIT_LOAN_CONTRACT = os.getenv("CREDIT_LOAN_CONTRACT", "0x0000000000000000000000000000000000000000")
RPC_URL = os.getenv("RPC_URL", "https://sepolia-rollup.arbitrum.io/rpc")  # Update for Arc network

# Contract ABI (simplified - you should use the full ABI from your compiled contract)
CREDIT_LOAN_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "loanId", "type": "uint256"},
            {"indexed": True, "name": "borrower", "type": "address"},
            {"indexed": False, "name": "principal", "type": "uint256"},
            {"indexed": False, "name": "serviceFee", "type": "uint256"},
            {"indexed": False, "name": "totalOwed", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
        ],
        "name": "LoanIssued",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "loanId", "type": "uint256"},
            {"indexed": True, "name": "borrower", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "remainingBalance", "type": "uint256"},
        ],
        "name": "RepaymentMade",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "loanId", "type": "uint256"},
            {"indexed": True, "name": "borrower", "type": "address"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
        ],
        "name": "LoanFullyRepaid",
        "type": "event",
    },
]


def store_transaction_in_db(
    db: Session,
    user_address: str,
    transaction_type: str,
    amount: Decimal,
    loan_id: Optional[int] = None,
    tx_hash: Optional[str] = None,
    block_number: Optional[int] = None,
    transaction_timestamp: Optional[datetime] = None,
    status: str = "confirmed",
    extra_metadata: Optional[str] = None,
) -> Transaction:
    """Store a transaction in the database."""
    if transaction_timestamp is None:
        transaction_timestamp = datetime.now(timezone.utc)
    
    transaction = Transaction(
        user_address=user_address.lower(),
        transaction_type=transaction_type,
        amount=amount,
        currency="USDC",
        loan_id=loan_id,
        tx_hash=tx_hash,
        block_number=block_number,
        transaction_timestamp=transaction_timestamp,
        status=status,
        extra_metadata=extra_metadata,
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


def sync_loan_issued_event(event: dict, db: Session) -> None:
    """Sync LoanIssued event to database."""
    args = event["args"]
    loan_id = args["loanId"]
    borrower = args["borrower"]
    principal = Decimal(args["principal"]) / Decimal(1e6)  # Convert from 6 decimals
    service_fee = Decimal(args["serviceFee"]) / Decimal(1e6)
    total_owed = Decimal(args["totalOwed"]) / Decimal(1e6)
    timestamp = datetime.fromtimestamp(args["timestamp"], tz=timezone.utc)
    
    # Store transaction
    store_transaction_in_db(
        db=db,
        user_address=borrower,
        transaction_type="loan_issued",
        amount=principal,
        loan_id=loan_id,
        tx_hash=event["transactionHash"].hex(),
        block_number=event["blockNumber"],
        transaction_timestamp=timestamp,
        status="confirmed",
        extra_metadata=f'{{"serviceFee": {service_fee}, "totalOwed": {total_owed}}}',
    )
    
    # Store or update loan history
    existing_loan = db.query(LoanHistory).filter(LoanHistory.loan_id == loan_id).first()
    if existing_loan:
        # Update existing loan
        existing_loan.principal = principal
        existing_loan.service_fee = service_fee
        existing_loan.total_owed = total_owed
        existing_loan.loan_timestamp = timestamp
        existing_loan.tx_hash = event["transactionHash"].hex()
        existing_loan.is_active = True
    else:
        # Create new loan
        loan = LoanHistory(
            loan_id=loan_id,
            user_address=borrower.lower(),
            principal=principal,
            service_fee=service_fee,
            total_owed=total_owed,
            amount_repaid=Decimal("0"),
            is_active=True,
            loan_timestamp=timestamp,
            tx_hash=event["transactionHash"].hex(),
        )
        db.add(loan)
    
    db.commit()
    print(f"✅ Synced LoanIssued: Loan #{loan_id} to {borrower[:10]}... for {principal} USDC")


def sync_repayment_event(event: dict, db: Session) -> None:
    """Sync RepaymentMade event to database."""
    args = event["args"]
    loan_id = args["loanId"]
    borrower = args["borrower"]
    amount = Decimal(args["amount"]) / Decimal(1e6)  # Convert from 6 decimals
    remaining_balance = Decimal(args["remainingBalance"]) / Decimal(1e6)
    
    # Get block timestamp
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    block = w3.eth.get_block(event["blockNumber"])
    timestamp = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc)
    
    # Store transaction
    store_transaction_in_db(
        db=db,
        user_address=borrower,
        transaction_type="repay",
        amount=amount,
        loan_id=loan_id,
        tx_hash=event["transactionHash"].hex(),
        block_number=event["blockNumber"],
        transaction_timestamp=timestamp,
        status="confirmed",
        extra_metadata=f'{{"remainingBalance": {remaining_balance}}}',
    )
    
    # Update loan history
    loan = db.query(LoanHistory).filter(LoanHistory.loan_id == loan_id).first()
    if loan:
        loan.amount_repaid = loan.total_owed - remaining_balance
        loan.is_active = remaining_balance > 0
        db.commit()
    
    print(f"✅ Synced Repayment: Loan #{loan_id}, {amount} USDC repaid, {remaining_balance} remaining")


def sync_loan_fully_repaid_event(event: dict, db: Session) -> None:
    """Sync LoanFullyRepaid event to database."""
    args = event["args"]
    loan_id = args["loanId"]
    borrower = args["borrower"]
    timestamp = datetime.fromtimestamp(args["timestamp"], tz=timezone.utc)
    
    # Update loan status
    loan = db.query(LoanHistory).filter(LoanHistory.loan_id == loan_id).first()
    if loan:
        loan.is_active = False
        loan.amount_repaid = loan.total_owed
        db.commit()
        print(f"✅ Synced LoanFullyRepaid: Loan #{loan_id} fully repaid")


def listen_to_events(start_block: Optional[int] = None) -> None:
    """Listen to blockchain events and sync to database."""
    print("🔍 Starting blockchain event listener...")
    print(f"   Contract: {CREDIT_LOAN_CONTRACT}")
    print(f"   RPC: {RPC_URL}")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect to blockchain RPC")
        return
    
    print("✅ Connected to blockchain")
    
    contract = w3.eth.contract(address=Web3.to_checksum_address(CREDIT_LOAN_CONTRACT), abi=CREDIT_LOAN_ABI)
    
    # Get start block (latest if not specified)
    if start_block is None:
        start_block = w3.eth.block_number - 1000  # Last 1000 blocks
    
    print(f"   Starting from block: {start_block}")
    
    db = SessionLocal()
    
    try:
        # Get past events
        print("\n📥 Fetching past events...")
        
        loan_issued_filter = contract.events.LoanIssued.create_filter(fromBlock=start_block)
        repayment_filter = contract.events.RepaymentMade.create_filter(fromBlock=start_block)
        fully_repaid_filter = contract.events.LoanFullyRepaid.create_filter(fromBlock=start_block)
        
        # Process LoanIssued events
        for event in loan_issued_filter.get_all_entries():
            try:
                sync_loan_issued_event(dict(event), db)
            except Exception as e:
                print(f"❌ Error syncing LoanIssued event: {e}")
        
        # Process RepaymentMade events
        for event in repayment_filter.get_all_entries():
            try:
                sync_repayment_event(dict(event), db)
            except Exception as e:
                print(f"❌ Error syncing RepaymentMade event: {e}")
        
        # Process LoanFullyRepaid events
        for event in fully_repaid_filter.get_all_entries():
            try:
                sync_loan_fully_repaid_event(dict(event), db)
            except Exception as e:
                print(f"❌ Error syncing LoanFullyRepaid event: {e}")
        
        print("\n✅ Past events synced!")
        print("\n💡 To listen for new events in real-time, run this script periodically or set up a cron job.")
        
    except Exception as e:
        print(f"❌ Error listening to events: {e}")
        raise
    finally:
        db.close()


def manual_sync_transaction(tx_hash: str) -> None:
    """Manually sync a specific transaction by hash."""
    print(f"🔍 Syncing transaction: {tx_hash}")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect to blockchain RPC")
        return
    
    try:
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
        contract = w3.eth.contract(address=Web3.to_checksum_address(CREDIT_LOAN_CONTRACT), abi=CREDIT_LOAN_ABI)
        
        db = SessionLocal()
        
        # Decode logs
        for log in tx_receipt["logs"]:
            try:
                event = contract.events.LoanIssued().process_log(log)
                sync_loan_issued_event(dict(event), db)
            except:
                pass
            
            try:
                event = contract.events.RepaymentMade().process_log(log)
                sync_repayment_event(dict(event), db)
            except:
                pass
            
            try:
                event = contract.events.LoanFullyRepaid().process_log(log)
                sync_loan_fully_repaid_event(dict(event), db)
            except:
                pass
        
        db.close()
        print("✅ Transaction synced!")
        
    except Exception as e:
        print(f"❌ Error syncing transaction: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync blockchain events to database")
    parser.add_argument("--start-block", type=int, help="Start block number")
    parser.add_argument("--tx-hash", type=str, help="Sync specific transaction hash")
    
    args = parser.parse_args()
    
    if args.tx_hash:
        manual_sync_transaction(args.tx_hash)
    else:
        listen_to_events(args.start_block)

