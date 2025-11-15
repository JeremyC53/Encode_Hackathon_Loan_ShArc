"""
Add a transaction via the API (simulates what happens when a user borrows/repays).
This uses the FastAPI endpoint to store the transaction.
"""
from __future__ import annotations

import requests
import json
from datetime import datetime, timezone, timedelta

BASE_URL = "http://localhost:8000/api"


def add_transaction_via_api():
    """Add a new transaction using the API endpoint."""
    print("🔄 Adding new transaction via API...")
    print(f"   API URL: {BASE_URL}")
    
    # Simulate a new loan issuance
    new_user = "0x9876543210fedcba9876543210fedcba98765432"
    loan_amount = 7500.0
    service_fee = 750.0
    total_owed = loan_amount + service_fee
    loan_id = 4  # Assuming we have loans 1-3 from sample data
    
    print(f"\n📝 Creating new loan transaction:")
    print(f"   User: {new_user}")
    print(f"   Loan ID: {loan_id}")
    print(f"   Amount: {loan_amount} USDC")
    
    # Create loan issuance transaction
    loan_transaction = {
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
        print("\n📤 Sending request to API...")
        response = requests.post(f"{BASE_URL}/transactions", json=loan_transaction)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Transaction created successfully!")
            print(f"   Transaction ID: {result['id']}")
            print(f"   User: {result['user_address']}")
            print(f"   Amount: {result['amount']} {result['currency']}")
            print(f"   Status: {result['status']}")
            
            # Now add a repayment
            print("\n📝 Creating repayment transaction...")
            repayment = {
                "user_address": new_user,
                "transaction_type": "repay",
                "amount": 2750.0,
                "currency": "USDC",
                "loan_id": loan_id,
                "tx_hash": f"0x{'c' * 64}",
                "block_number": 5100,
                "transaction_timestamp": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "status": "confirmed",
                "extra_metadata": json.dumps({
                    "remainingBalance": total_owed - 2750.0
                })
            }
            
            response2 = requests.post(f"{BASE_URL}/transactions", json=repayment)
            if response2.status_code == 201:
                result2 = response2.json()
                print(f"✅ Repayment transaction created!")
                print(f"   Transaction ID: {result2['id']}")
                print(f"   Amount: {result2['amount']} {result2['currency']}")
            
            print(f"\n🔍 Verify in Supabase:")
            print(f"   Dashboard: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd")
            print(f"   Table: transactions")
            
            print(f"\n🔍 Or query via API:")
            print(f"   GET {BASE_URL}/transactions")
            print(f"   GET {BASE_URL}/users/{new_user}/transactions")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server.")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 Add Transaction via API")
    print("=" * 60)
    print()
    
    success = add_transaction_via_api()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Transaction added! Check Supabase dashboard.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Failed to add transaction. Check errors above.")
        print("=" * 60)

