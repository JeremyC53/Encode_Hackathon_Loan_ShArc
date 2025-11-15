from fastapi import APIRouter, Header, HTTPException

from .schemas import (
    AuthRequest,
    AuthResponse,
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


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="Loan ShArc backend is running")


@router.post("/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: AuthRequest) -> AuthResponse:
    try:
        record, user_token, encryption_key, challenge_id = sign_up_user(
            payload.email, payload.password
        )
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
        record, user_token, encryption_key, challenge_id = sign_in_user(
            payload.email, payload.password
        )
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
