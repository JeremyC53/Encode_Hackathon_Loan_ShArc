from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PlatformTransaction(BaseModel):
    id: Optional[str] = None
    timestamp: Optional[str] = None
    grossAmount: Optional[str] = None
    netAmount: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    city: Optional[str] = None


class PlatformSummary(BaseModel):
    totalEarnedUsdc: int = Field(..., description="Aggregated earnings in 6-decimal USDC units")
    csvSampleCount: int
    lastPayoutDate: Optional[str] = None
    lastPayoutEpoch: Optional[int] = None
    onTimeRatioBps: Optional[int] = Field(
        None, description="On-time payment ratio represented in basis points"
    )


class PlatformEntry(BaseModel):
    platform: str
    currency: str
    sourceCsv: Optional[str] = None
    fxRateSource: Optional[str] = None
    fxRateUsdPerGbp: Optional[str] = None
    transactions: List[PlatformTransaction] = Field(default_factory=list)
    summary: PlatformSummary


class AggregateMetrics(BaseModel):
    totalEarnedUsdc: Optional[int] = None
    platformCount: Optional[int] = None
    averageMonthlyIncomeUsdc: Optional[int] = None
    weightedOnTimeRatioBps: Optional[int] = None
    totalCsvSampleCount: Optional[int] = None
    sourceScript: Optional[str] = None


class FreelanceHistoryPayload(BaseModel):
    freelancerAddress: str
    snapshotTimestamp: str
    snapshotTimestampEpoch: int
    lookbackMonths: int
    platforms: List[PlatformEntry]
    aggregateMetrics: Optional[AggregateMetrics] = None


class HealthResponse(BaseModel):
    status: str
    message: str


class FreelancePreviewResponse(BaseModel):
    platformCount: int
    totalEarnedUsdc: int
    lookbackMonths: int
    snapshotTimestampEpoch: int
    message: str


# Transaction schemas
class TransactionCreate(BaseModel):
    user_address: str
    transaction_type: str  # 'borrow', 'repay', 'loan_issued', etc.
    amount: float
    currency: str = "USDC"
    loan_id: Optional[int] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    transaction_timestamp: Optional[str] = None  # ISO format datetime, defaults to now if not provided
    status: str = "pending"
    extra_metadata: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    user_address: str
    transaction_type: str
    amount: float
    currency: str
    loan_id: Optional[int] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    created_at: str
    transaction_timestamp: str
    status: str
    extra_metadata: Optional[str] = None

    class Config:
        from_attributes = True


class LoanHistoryResponse(BaseModel):
    id: int
    loan_id: int
    user_address: str
    principal: float
    service_fee: float
    total_owed: float
    amount_repaid: float
    is_active: bool
    created_at: str
    loan_timestamp: str
    last_updated: str
    tx_hash: Optional[str] = None
    credit_score_at_issuance: Optional[int] = None
    apr_bps: Optional[int] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int