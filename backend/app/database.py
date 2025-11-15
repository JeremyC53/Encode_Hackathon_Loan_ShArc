from __future__ import annotations

from typing import Dict, Optional

from .models import WalletUser

_USERS: Dict[str, WalletUser] = {}
_USERS_BY_ID: Dict[str, WalletUser] = {}


def _normalize(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(email: str) -> Optional[WalletUser]:
    return _USERS.get(_normalize(email))


def get_user_by_circle_id(circle_user_id: str) -> Optional[WalletUser]:
    return _USERS_BY_ID.get(circle_user_id)


def save_user(record: WalletUser) -> WalletUser:
    _USERS[_normalize(record.email)] = record
    _USERS_BY_ID[record.circle_user_id] = record
    return record

