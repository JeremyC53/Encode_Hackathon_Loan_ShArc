from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WalletUser:
    email: str
    circle_user_id: str
    password_hash: str = ""
    encryption_key: str = ""
    wallet_set_id: str = ""
    wallet_id: str = ""
    wallet_address: str = ""
