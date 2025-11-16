from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .schemas import FreelanceHistoryPayload, FreelancePreviewResponse, HealthResponse
from .contract_service import contract_service

router = APIRouter(prefix="/api", tags=["api"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_HISTORY_PATH = (
    PROJECT_ROOT / "blockchain" / "hello-arc" / "data" / "sample_freelancer_history.json"
)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Quick liveness probe for uptime checks.
    """
    return HealthResponse(status="ok", message="Loan ShArc backend is running")


def _load_sample_history() -> FreelanceHistoryPayload:
    if not SAMPLE_HISTORY_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Sample history is missing at {SAMPLE_HISTORY_PATH}",
        )
    with SAMPLE_HISTORY_PATH.open("r", encoding="utf-8") as infile:
        try:
            data = json.load(infile)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Sample JSON is invalid") from exc
    return FreelanceHistoryPayload(**data)


@router.get("/freelancers/sample", response_model=FreelanceHistoryPayload)
def fetch_sample_history() -> FreelanceHistoryPayload:
    """
    Returns the static JSON snapshot generated from Gmail exports.
    """
    return _load_sample_history()


def _summarize_history(payload: FreelanceHistoryPayload) -> FreelancePreviewResponse:
    total_earned = sum(
        platform.summary.totalEarnedUsdc for platform in payload.platforms
    )
    platform_count = len(payload.platforms)
    message = (
        "History received. Wire this response into on-chain scoring when ready."
    )
    return FreelancePreviewResponse(
        platformCount=platform_count,
        totalEarnedUsdc=total_earned,
        lookbackMonths=payload.lookbackMonths,
        snapshotTimestampEpoch=payload.snapshotTimestampEpoch,
        message=message,
    )


@router.post(
    "/freelancers/preview",
    response_model=FreelancePreviewResponse,
    summary="Validate parsed Gmail data before calling the smart contract",
)
def preview_freelance_history(payload: FreelanceHistoryPayload) -> FreelancePreviewResponse:
    """
    Accepts a `FreelanceHistoryPayload` (usually produced by the Gmail parser) and
    returns a lightweight summary that can later be fed into the on-chain
    `FreelanceCreditScorer`.
    """
    return _summarize_history(payload)


# ============================================================================
# Blockchain / Smart Contract Endpoints (Arc Testnet)
# ============================================================================

class IssueLoanRequest(BaseModel):
    """Request model for issuing a new loan"""
    borrower_address: str
    principal: float
    wait_for_confirmation: bool = False  # Optional: wait for tx to be mined


class RepayLoanRequest(BaseModel):
    """Request model for loan repayment"""
    loan_id: int
    amount: float


class FundContractRequest(BaseModel):
    """Request model for funding the contract with USDC"""
    amount: float
    wait_for_confirmation: bool = False  # Optional: wait for tx to be mined


class LoanDetailsResponse(BaseModel):
    """Response model for loan details"""
    id: int
    borrower: str
    principal: float
    service_fee: float
    total_owed: float
    amount_repaid: float
    timestamp: int
    active: bool


@router.get("/blockchain/wallet")
def get_wallet_info():
    """
    Get backend wallet information (address, balance, pending transactions)
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        return contract_service.get_wallet_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blockchain/transaction/{tx_hash}")
def get_transaction_status(tx_hash: str):
    """
    Check the status of a transaction by hash
    
    Returns transaction status: success, failed, pending, or not_found
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        return contract_service.get_transaction_status(tx_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/balance")
def get_loan_balance(loan_id: int):
    """
    Get remaining balance for a specific loan
    
    This is a read-only operation (no gas required)
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        balance = contract_service.get_remaining_balance(loan_id)
        return {
            "loan_id": loan_id,
            "remaining_balance": balance,
            "currency": "USDC"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/borrower/{address}")
def get_borrower_loans_endpoint(address: str):
    """
    Get all loan IDs for a borrower address
    
    This is a read-only operation (no gas required)
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        loan_ids = contract_service.get_borrower_loans(address)
        return {
            "borrower": address,
            "loan_ids": loan_ids,
            "count": len(loan_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/borrower/{address}/details")
def get_borrower_loans_with_details(address: str):
    """
    Get all loans with full details for a borrower address
    
    This endpoint:
    1. Gets all loan IDs for the borrower using getBorrowerLoans()
    2. Fetches detailed information for each loan using loans() function
    3. Returns complete loan data including principal, fees, repayment status, etc.
    
    This is a read-only operation (no gas required)
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        # Get all loan IDs for the borrower
        loan_ids = contract_service.get_borrower_loans(address)
        
        # Fetch details for each loan
        loans_details = []
        for loan_id in loan_ids:
            try:
                loan_detail = contract_service.get_loan_details(loan_id)
                loans_details.append(loan_detail)
            except Exception as e:
                # If a specific loan fails, log it but continue with others
                print(f"Warning: Failed to fetch details for loan {loan_id}: {str(e)}")
                continue
        
        return {
            "borrower": address,
            "loan_count": len(loans_details),
            "loans": loans_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/details", response_model=LoanDetailsResponse)
def get_loan_details_endpoint(loan_id: int):
    """
    Get detailed information about a specific loan
    
    This is a read-only operation (no gas required)
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        details = contract_service.get_loan_details(loan_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/issue")
def issue_loan_endpoint(request: IssueLoanRequest):
    """
    Issue a new loan to a borrower
    
    This operation writes to the blockchain and requires gas (paid in USDC on Arc)
    The backend wallet will create a new loan with the specified principal.
    
    Following best practices from:
    https://ethereum.stackexchange.com/questions/134720/execute-a-contract-function-from-web3-py
    
    Parameters:
    - borrower_address: The wallet address of the borrower
    - principal: The principal amount in USDC
    - wait_for_confirmation: (Optional) Wait for transaction to be mined (default: False)
    
    Response:
    - If wait_for_confirmation=False: Returns immediately with tx_hash (status: "submitted")
    - If wait_for_confirmation=True: Waits up to 60s for confirmation (status: "success", "failed", or "pending")
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.issue_loan(
            request.borrower_address, 
            request.principal,
            request.wait_for_confirmation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/repay")
def repay_loan_endpoint(request: RepayLoanRequest):
    """
    Repay a loan from the backend wallet
    
    This operation writes to the blockchain and requires gas (paid in USDC on Arc)
    The backend wallet will automatically approve USDC if needed.
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.repay_loan(request.loan_id, request.amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/approve-usdc")
def approve_usdc_endpoint(amount: float):
    """
    Approve USDC spending by the CreditLoan contract
    
    This is usually called automatically by the repay endpoint, but can be called manually
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.approve_usdc(amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/fund")
def fund_contract_endpoint(request: FundContractRequest):
    """
    Fund the CreditLoan contract with USDC from the backend wallet
    
    This operation writes to the blockchain and requires gas (paid in USDC on Arc)
    The backend wallet will transfer USDC to the contract to provide liquidity for loans.
    
    Only the contract owner (backend wallet) can call this function.
    
    Parameters:
    - amount: The amount of USDC to fund (as a float, e.g., 1000.0 for 1000 USDC)
    - wait_for_confirmation: (Optional) Wait for transaction to be mined (default: False)
    
    Response:
    - If wait_for_confirmation=False: Returns immediately with tx_hash (status: "submitted")
    - If wait_for_confirmation=True: Waits up to 60s for confirmation (status: "success", "failed", or "pending")
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.fund_contract(
            request.amount,
            request.wait_for_confirmation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Credit Score Endpoints
# ============================================================================

class SetCreditScoreRequest(BaseModel):
    """Request model for setting credit score"""
    user_address: str
    score: int
    wait_for_confirmation: bool = False  # Optional: wait for tx to be mined


@router.post("/credit-score/set")
def set_credit_score_endpoint(request: SetCreditScoreRequest):
    """
    Set credit score for a user address
    
    This operation writes to the blockchain and requires gas (paid in USDC on Arc)
    Only the admin (backend wallet) can call this function.
    
    Parameters:
    - user_address: The wallet address of the user (required)
    - score: The credit score to set as uint256 (required, must be > 0)
    - wait_for_confirmation: (Optional) Wait for transaction to be mined (default: False)
    
    Response:
    - If wait_for_confirmation=False: Returns immediately with tx_hash (status: "submitted")
    - If wait_for_confirmation=True: Waits up to 60s for confirmation (status: "success", "failed", or "pending")
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.set_credit_score(
            request.user_address,
            request.score,
            request.wait_for_confirmation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credit-score/{address}")
def get_credit_score_endpoint(address: str):
    """
    Get credit score for a user address
    
    This is a read-only operation (no gas required)
    
    Returns the credit score and the timestamp of when it was last updated
    """
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env"
        )
    try:
        result = contract_service.get_credit_score(address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
