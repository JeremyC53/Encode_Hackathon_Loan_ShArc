from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db
from .models import Transaction, LoanHistory
from .schemas import (
    FreelanceHistoryPayload,
    FreelancePreviewResponse,
    HealthResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    LoanHistoryResponse,
)

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


# Transaction endpoints
@router.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Create a new transaction record.
    Use this to log borrows, repayments, and other loan-related transactions.
    """
    try:
        # Parse transaction timestamp
        try:
            # Try to parse ISO format timestamp
            if transaction.transaction_timestamp:
                tx_timestamp = datetime.fromisoformat(
                    transaction.transaction_timestamp.replace("Z", "+00:00")
                )
            else:
                tx_timestamp = datetime.utcnow()
        except (ValueError, AttributeError) as e:
            # Fall back to current time if parsing fails
            tx_timestamp = datetime.utcnow()

        # Validate user address format
        user_address = transaction.user_address.strip().lower()
        if not user_address.startswith("0x") or len(user_address) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user address format: {transaction.user_address}"
            )

        # Create transaction record
        db_transaction = Transaction(
            user_address=user_address,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            currency=transaction.currency or "USDC",
            loan_id=transaction.loan_id,
            tx_hash=transaction.tx_hash,
            block_number=transaction.block_number,
            transaction_timestamp=tx_timestamp,
            status=transaction.status or "pending",
            extra_metadata=transaction.extra_metadata,
        )

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        return TransactionResponse(
            id=db_transaction.id,
            user_address=db_transaction.user_address,
            transaction_type=db_transaction.transaction_type,
            amount=float(db_transaction.amount),
            currency=db_transaction.currency,
            loan_id=db_transaction.loan_id,
            tx_hash=db_transaction.tx_hash,
            block_number=db_transaction.block_number,
            created_at=db_transaction.created_at.isoformat(),
            transaction_timestamp=db_transaction.transaction_timestamp.isoformat(),
            status=db_transaction.status,
            extra_metadata=db_transaction.extra_metadata,
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        # Log the error and return a 500 with details
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating transaction: {error_details}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    user_address: Optional[str] = Query(None, description="Filter by user address"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    loan_id: Optional[int] = Query(None, description="Filter by loan ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """
    Get transaction history with optional filters.
    Supports pagination and filtering by user, type, and loan ID.
    """
    query = db.query(Transaction)

    # Apply filters
    if user_address:
        query = query.filter(Transaction.user_address == user_address.lower())
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if loan_id:
        query = query.filter(Transaction.loan_id == loan_id)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    transactions = (
        query.order_by(desc(Transaction.transaction_timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response format
    transaction_responses = [
        TransactionResponse(
            id=tx.id,
            user_address=tx.user_address,
            transaction_type=tx.transaction_type,
            amount=float(tx.amount),
            currency=tx.currency,
            loan_id=tx.loan_id,
            tx_hash=tx.tx_hash,
            block_number=tx.block_number,
            created_at=tx.created_at.isoformat(),
            transaction_timestamp=tx.transaction_timestamp.isoformat(),
            status=tx.status,
            extra_metadata=tx.extra_metadata,
        )
        for tx in transactions
    ]

    return TransactionListResponse(
        transactions=transaction_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Get a specific transaction by ID."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse(
        id=transaction.id,
        user_address=transaction.user_address,
        transaction_type=transaction.transaction_type,
        amount=float(transaction.amount),
        currency=transaction.currency,
        loan_id=transaction.loan_id,
        tx_hash=transaction.tx_hash,
        block_number=transaction.block_number,
        created_at=transaction.created_at.isoformat(),
        transaction_timestamp=transaction.transaction_timestamp.isoformat(),
        status=transaction.status,
        extra_metadata=transaction.extra_metadata,
    )


@router.get("/users/{user_address}/transactions", response_model=TransactionListResponse)
def get_user_transactions(
    user_address: str,
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """
    Get all transactions for a specific user.
    Convenience endpoint that filters by user address.
    """
    return get_transactions(
        user_address=user_address,
        transaction_type=transaction_type,
        page=page,
        page_size=page_size,
        db=db,
    )


@router.get("/loans/{loan_id}/transactions", response_model=TransactionListResponse)
def get_loan_transactions(
    loan_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """
    Get all transactions for a specific loan.
    """
    return get_transactions(
        loan_id=loan_id,
        page=page,
        page_size=page_size,
        db=db,
    )


# Loan history endpoints
@router.get("/loans", response_model=list[LoanHistoryResponse])
def get_loans(
    user_address: Optional[str] = Query(None, description="Filter by user address"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
) -> list[LoanHistoryResponse]:
    """
    Get loan history with optional filters.
    """
    query = db.query(LoanHistory)

    if user_address:
        query = query.filter(LoanHistory.user_address == user_address.lower())
    if is_active is not None:
        query = query.filter(LoanHistory.is_active == is_active)

    loans = query.order_by(desc(LoanHistory.loan_timestamp)).all()

    return [
        LoanHistoryResponse(
            id=loan.id,
            loan_id=loan.loan_id,
            user_address=loan.user_address,
            principal=float(loan.principal),
            service_fee=float(loan.service_fee),
            total_owed=float(loan.total_owed),
            amount_repaid=float(loan.amount_repaid),
            is_active=loan.is_active,
            created_at=loan.created_at.isoformat(),
            loan_timestamp=loan.loan_timestamp.isoformat(),
            last_updated=loan.last_updated.isoformat(),
            tx_hash=loan.tx_hash,
            credit_score_at_issuance=loan.credit_score_at_issuance,
            apr_bps=loan.apr_bps,
        )
        for loan in loans
    ]


@router.get("/users/{user_address}/loans", response_model=list[LoanHistoryResponse])
def get_user_loans(
    user_address: str,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
) -> list[LoanHistoryResponse]:
    """
    Get all loans for a specific user.
    """
    query = db.query(LoanHistory).filter(LoanHistory.user_address == user_address.lower())
    
    if is_active is not None:
        query = query.filter(LoanHistory.is_active == is_active)
    
    loans = query.order_by(desc(LoanHistory.loan_timestamp)).all()
    
    return [
        LoanHistoryResponse(
            id=loan.id,
            loan_id=loan.loan_id,
            user_address=loan.user_address,
            principal=float(loan.principal),
            service_fee=float(loan.service_fee),
            total_owed=float(loan.total_owed),
            amount_repaid=float(loan.amount_repaid),
            is_active=loan.is_active,
            created_at=loan.created_at.isoformat(),
            loan_timestamp=loan.loan_timestamp.isoformat(),
            last_updated=loan.last_updated.isoformat(),
            tx_hash=loan.tx_hash,
            credit_score_at_issuance=loan.credit_score_at_issuance,
            apr_bps=loan.apr_bps,
        )
        for loan in loans
    ]
