from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .schemas import FreelanceHistoryPayload, FreelancePreviewResponse, HealthResponse

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
