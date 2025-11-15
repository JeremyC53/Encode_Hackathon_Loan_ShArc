from typing import Optional

from pydantic import BaseModel, EmailStr


class HealthResponse(BaseModel):
    status: str
    message: str


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
