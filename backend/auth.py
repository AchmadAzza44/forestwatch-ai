"""Peran sederhana berbasis token (PRD: akses pengelolaan data dibatasi sesuai peran).

- viewer: tanpa token, hanya endpoint baca.
- operator: header `X-API-Key` = OPERATOR_TOKEN -> boleh memverifikasi indikasi.
- admin: header `X-API-Key` = ADMIN_TOKEN -> boleh juga mengelola (mis. impor).
Token kosong pada konfigurasi berarti peran itu dinonaktifkan. Ini autentikasi dasar untuk MVP, bukan sistem identitas penuh:
tidak ada akun per pengguna, rotasi, atau pembatasan laju; gunakan HTTPS dan token acak panjang pada deployment.
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Header, HTTPException

from config import settings

ROLE_ORDER = {"viewer": 0, "operator": 1, "admin": 2}


def resolve_role(api_key: Optional[str]) -> str:
    if not api_key:
        return "viewer"
    for role, token in (("admin", settings.ADMIN_TOKEN), ("operator", settings.OPERATOR_TOKEN)):
        if token and secrets.compare_digest(api_key.encode(), token.encode()):
            return role
    raise HTTPException(status_code=401, detail="Token tidak valid.")


def require_role(minimum: str):
    def dependency(x_api_key: Optional[str] = Header(default=None)) -> str:
        role = resolve_role(x_api_key)
        if ROLE_ORDER[role] < ROLE_ORDER[minimum]:
            raise HTTPException(status_code=403, detail=f"Memerlukan peran {minimum}.")
        return role

    return dependency
