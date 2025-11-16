from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Health and freelance data structures (from the reference commit)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Circle wallet / authentication payloads (existing branch functionality)
# ---------------------------------------------------------------------------


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    circle_user_id: str
    user_token: str
    encryption_key: Optional[str] = None
    challenge_id: Optional[str] = None
    wallet_address: Optional[str] = None
    wallet_id: Optional[str] = None
    wallet_set_id: Optional[str] = None


class PinRestoreResponse(BaseModel):
    challenge_id: str


class WalletSyncRequest(BaseModel):
    circle_user_id: str
    user_token: Optional[str] = None


class WalletSyncResponse(BaseModel):
    wallet_address: str
    wallet_id: str
    wallet_set_id: str
