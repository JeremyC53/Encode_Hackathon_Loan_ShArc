"""
SQLAlchemy database models for transaction and loan history.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func

from .database import Base


class Transaction(Base):
    """
    Stores all on-chain and off-chain transactions related to loans.
    Includes borrows, repayments, and other loan-related activities.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    user_address = Column(String(66), nullable=False, index=True)  # Ethereum address (0x...) - using 66 to match tx_hash length
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False, index=True)  # 'borrow', 'repay', 'loan_issued', etc.
    amount = Column(Numeric(20, 6), nullable=False)  # Amount in USDC (6 decimals)
    currency = Column(String(10), default="USDC", nullable=False)  # Currency code
    
    # Loan reference
    loan_id = Column(Integer, nullable=True, index=True)  # Reference to on-chain loan ID
    
    # Blockchain details
    tx_hash = Column(String(66), nullable=True, unique=True, index=True)  # On-chain transaction hash
    block_number = Column(Integer, nullable=True)  # Block number if on-chain
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transaction_timestamp = Column(DateTime(timezone=True), nullable=False)  # When transaction actually occurred
    
    # Status and metadata
    status = Column(String(20), default="pending", nullable=False)  # 'pending', 'confirmed', 'failed'
    extra_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_user_type", "user_address", "transaction_type"),
        Index("idx_user_created", "user_address", "created_at"),
        Index("idx_loan_id", "loan_id"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, user={self.user_address[:10]}..., type={self.transaction_type}, amount={self.amount})>"


class LoanHistory(Base):
    """
    Stores loan information synced from blockchain.
    This provides a queryable off-chain view of loan data.
    """
    __tablename__ = "loan_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Loan identification
    loan_id = Column(Integer, unique=True, nullable=False, index=True)  # On-chain loan ID
    user_address = Column(String(66), nullable=False, index=True)
    
    # Loan terms
    principal = Column(Numeric(20, 6), nullable=False)  # Original loan amount
    service_fee = Column(Numeric(20, 6), nullable=False)  # Service fee amount
    total_owed = Column(Numeric(20, 6), nullable=False)  # Principal + service fee
    amount_repaid = Column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    loan_timestamp = Column(DateTime(timezone=True), nullable=False)  # When loan was issued on-chain
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Blockchain reference
    tx_hash = Column(String(66), nullable=True)  # Transaction hash of loan issuance
    
    # Additional metadata
    credit_score_at_issuance = Column(Integer, nullable=True)  # Credit score when loan was issued
    apr_bps = Column(Integer, nullable=True)  # APR in basis points
    
    def __repr__(self) -> str:
        return f"<LoanHistory(loan_id={self.loan_id}, user={self.user_address[:10]}..., principal={self.principal})>"


class CreditScoreHistory(Base):
    """
    Tracks credit score changes over time for users.
    """
    __tablename__ = "credit_score_history"

    id = Column(Integer, primary_key=True, index=True)
    
    user_address = Column(String(66), nullable=False, index=True)
    credit_score = Column(Integer, nullable=False)
    
    # Source of the score
    source = Column(String(50), default="freelance_scorer", nullable=False)  # 'freelance_scorer', 'manual', etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    score_timestamp = Column(DateTime(timezone=True), nullable=False)  # When score was calculated
    
    # Metadata
    extra_metadata = Column(Text, nullable=True)  # JSON string for additional context
    
    # Index for querying user's score history
    __table_args__ = (
        Index("idx_user_score_time", "user_address", "score_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<CreditScoreHistory(user={self.user_address[:10]}..., score={self.credit_score}, at={self.score_timestamp})>"

