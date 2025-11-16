from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .contract_service import contract_service
from .schemas import (
    AuthRequest,
    AuthResponse,
    FreelanceHistoryPayload,
    FreelancePreviewResponse,
    HealthResponse,
    PinRestoreResponse,
    WalletSyncRequest,
    WalletSyncResponse,
)
from .services.auth import (
    AuthServiceError,
    InvalidCredentials,
    UserAlreadyExists,
    WalletNotInitialized,
    restore_pin_challenge,
    sign_in_user,
    sign_up_user,
    sync_wallet_metadata,
)

router = APIRouter(prefix="/api", tags=["api"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_HISTORY_PATH = PROJECT_ROOT / "blockchain" / "hello-arc" / "data" / "sample_freelancer_history.json"


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
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
    total_earned = sum(platform.summary.totalEarnedUsdc for platform in payload.platforms)
    platform_count = len(payload.platforms)
    message = "History received. Wire this response into on-chain scoring when ready."
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
    Accepts a `FreelanceHistoryPayload` (usually produced by the Gmail parser)
    and returns a lightweight summary that can later be fed into the
    on-chain `FreelanceCreditScorer`.
    """
    return _summarize_history(payload)


# ---------------------------------------------------------------------------
# Circle wallet authentication endpoints
# ---------------------------------------------------------------------------


@router.post("/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: AuthRequest) -> AuthResponse:
    try:
        record, user_token, encryption_key, challenge_id = sign_up_user(payload.email, payload.password)
    except UserAlreadyExists as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AuthServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AuthResponse(
        circle_user_id=record.circle_user_id,
        user_token=user_token,
        encryption_key=encryption_key,
        challenge_id=challenge_id,
        wallet_address=record.wallet_address or None,
        wallet_id=record.wallet_id or None,
        wallet_set_id=record.wallet_set_id or None,
    )


@router.post("/auth/signin", response_model=AuthResponse)
def signin(payload: AuthRequest) -> AuthResponse:
    try:
        record, user_token, encryption_key, challenge_id = sign_in_user(payload.email, payload.password)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AuthResponse(
        circle_user_id=record.circle_user_id,
        user_token=user_token,
        encryption_key=encryption_key,
        challenge_id=challenge_id,
        wallet_address=record.wallet_address or None,
        wallet_id=record.wallet_id or None,
        wallet_set_id=record.wallet_set_id or None,
    )


@router.post("/auth/pin/restore", response_model=PinRestoreResponse)
def restore_pin(x_user_token: str = Header(..., alias="X-User-Token")) -> PinRestoreResponse:
    try:
        challenge_id = restore_pin_challenge(x_user_token)
    except AuthServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return PinRestoreResponse(challenge_id=challenge_id)


@router.post("/wallets/sync", response_model=WalletSyncResponse)
def sync_wallet(payload: WalletSyncRequest) -> WalletSyncResponse:
    try:
        record = sync_wallet_metadata(payload.circle_user_id, payload.user_token or "")
    except WalletNotInitialized as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AuthServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return WalletSyncResponse(
        wallet_address=record.wallet_address,
        wallet_id=record.wallet_id,
        wallet_set_id=record.wallet_set_id,
    )


# ---------------------------------------------------------------------------
# Blockchain helper endpoints mirroring the reference commit
# ---------------------------------------------------------------------------


class IssueLoanRequest(BaseModel):
    borrower_address: str
    principal: float
    wait_for_confirmation: bool = False


class RepayLoanRequest(BaseModel):
    loan_id: int
    amount: float


class FundContractRequest(BaseModel):
    amount: float
    wait_for_confirmation: bool = False


class LoanDetailsResponse(BaseModel):
    id: int
    borrower: str
    principal: float
    service_fee: float
    total_owed: float
    amount_repaid: float
    timestamp: int
    active: bool


def _require_contract_service():
    if not contract_service:
        raise HTTPException(
            status_code=503,
            detail="Contract service not initialized. Check WALLET_PRIVATE_KEY in .env",
        )


@router.get("/blockchain/wallet")
def get_wallet_info():
    _require_contract_service()
    try:
        return contract_service.get_wallet_info()
    except Exception as exc:  # pragma: no cover - best effort logging path
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/blockchain/transaction/{tx_hash}")
def get_transaction_status(tx_hash: str):
    _require_contract_service()
    try:
        return contract_service.get_transaction_status(tx_hash)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/loans/{loan_id}/balance")
def get_loan_balance(loan_id: int):
    _require_contract_service()
    try:
        balance = contract_service.get_remaining_balance(loan_id)
        return {"loan_id": loan_id, "remaining_balance": balance, "currency": "USDC"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/loans/borrower/{address}")
def get_borrower_loans_endpoint(address: str):
    _require_contract_service()
    try:
        loan_ids = contract_service.get_borrower_loans(address)
        return {"borrower": address, "loan_ids": loan_ids, "count": len(loan_ids)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/loans/{loan_id}/details", response_model=LoanDetailsResponse)
def get_loan_details_endpoint(loan_id: int):
    _require_contract_service()
    try:
        details = contract_service.get_loan_details(loan_id)
        return details
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/loans/issue")
def issue_loan_endpoint(request: IssueLoanRequest):
    _require_contract_service()
    try:
        result = contract_service.issue_loan(
            request.borrower_address,
            request.principal,
            request.wait_for_confirmation,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/loans/repay")
def repay_loan_endpoint(request: RepayLoanRequest):
    _require_contract_service()
    try:
        result = contract_service.repay_loan(request.loan_id, request.amount)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/loans/approve-usdc")
def approve_usdc_endpoint(amount: float):
    _require_contract_service()
    try:
        result = contract_service.approve_usdc(amount)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/loans/fund")
def fund_contract_endpoint(request: FundContractRequest):
    _require_contract_service()
    try:
        result = contract_service.fund_contract(
            request.amount,
            request.wait_for_confirmation,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
