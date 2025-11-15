"""
Example script showing how to use the database API.
Run this after starting the FastAPI server.
"""
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000/api"

# Example: Create a transaction
def create_transaction_example():
    """Example of creating a transaction record."""
    transaction_data = {
        "user_address": "0x1234567890abcdef1234567890abcdef12345678",
        "transaction_type": "borrow",
        "amount": 1000.50,
        "currency": "USDC",
        "loan_id": 1,
        "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "block_number": 12345,
        "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed",
        "metadata": '{"source": "blockchain_event"}'
    }
    
    response = requests.post(f"{BASE_URL}/transactions", json=transaction_data)
    print("Created transaction:", response.json())
    return response.json()["id"]


# Example: Get user's transactions
def get_user_transactions_example():
    """Example of querying transactions for a user."""
    user_address = "0x1234567890abcdef1234567890abcdef12345678"
    
    # Get all transactions
    response = requests.get(f"{BASE_URL}/users/{user_address}/transactions")
    print(f"\nAll transactions for {user_address}:")
    print(response.json())
    
    # Get only repayments
    response = requests.get(
        f"{BASE_URL}/users/{user_address}/transactions",
        params={"transaction_type": "repay"}
    )
    print(f"\nRepayments only:")
    print(response.json())


# Example: Get loan transactions
def get_loan_transactions_example():
    """Example of getting all transactions for a specific loan."""
    loan_id = 1
    response = requests.get(f"{BASE_URL}/loans/{loan_id}/transactions")
    print(f"\nTransactions for loan {loan_id}:")
    print(response.json())


# Example: Create multiple transactions for a loan lifecycle
def loan_lifecycle_example():
    """Example of tracking a complete loan lifecycle."""
    user_address = "0x1234567890abcdef1234567890abcdef12345678"
    loan_id = 1
    now = datetime.now(timezone.utc)
    
    # 1. Loan issued
    requests.post(f"{BASE_URL}/transactions", json={
        "user_address": user_address,
        "transaction_type": "loan_issued",
        "amount": 5000.0,
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": "0x111...",
        "transaction_timestamp": now.isoformat(),
        "status": "confirmed"
    })
    
    # 2. First repayment
    requests.post(f"{BASE_URL}/transactions", json={
        "user_address": user_address,
        "transaction_type": "repay",
        "amount": 1000.0,
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": "0x222...",
        "transaction_timestamp": (now.replace(day=now.day + 30)).isoformat(),
        "status": "confirmed"
    })
    
    # 3. Second repayment
    requests.post(f"{BASE_URL}/transactions", json={
        "user_address": user_address,
        "transaction_type": "repay",
        "amount": 1000.0,
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": "0x333...",
        "transaction_timestamp": (now.replace(day=now.day + 60)).isoformat(),
        "status": "confirmed"
    })
    
    # Get all transactions for this loan
    response = requests.get(f"{BASE_URL}/loans/{loan_id}/transactions")
    print("\nLoan lifecycle transactions:")
    for tx in response.json()["transactions"]:
        print(f"  {tx['transaction_type']}: {tx['amount']} {tx['currency']} on {tx['transaction_timestamp']}")


if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("\n" + "="*50)
    
    # Uncomment to run examples:
    # create_transaction_example()
    # get_user_transactions_example()
    # get_loan_transactions_example()
    # loan_lifecycle_example()
    
    print("\nExamples ready to run. Uncomment the function calls above.")

