from __future__ import annotations

import base64
import json
from dataclasses import dataclass


class HttpAuthError(Exception):
    def __init__(self, status_code: int, detail: object) -> None:
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str  # "user" | "admin"
    instagram_user_id: str | None = None


def _decode_test_bearer(authorization: str | None) -> Principal:
    """Decode Bearer token: base64url JSON for tests and local dev."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HttpAuthError(401, "Missing or invalid Authorization header")
    raw = authorization.removeprefix("Bearer ").strip()
    padded = raw + "=" * (-len(raw) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
    except (json.JSONDecodeError, ValueError) as e:
        raise HttpAuthError(401, "Invalid bearer token") from e
    role = payload.get("role")
    sub = payload.get("sub")
    if not role or not sub:
        raise HttpAuthError(401, "Token missing role or sub")
    if role not in ("user", "admin"):
        raise HttpAuthError(401, "Invalid role")
    ig = payload.get("instagram_user_id")
    return Principal(subject=sub, role=role, instagram_user_id=ig)


def require_user_principal(authorization: str | None) -> Principal:
    p = _decode_test_bearer(authorization)
    if p.role != "user":
        raise HttpAuthError(403, "User role required")
    if not p.instagram_user_id:
        raise HttpAuthError(
            400,
            {
                "code": "instagram_not_linked",
                "message": "Connect Instagram before transferring.",
                "remediation": {
                    "action": "oauth_instagram",
                    "docs": "/v1/oauth/instagram",
                },
            },
        )
    return p


def require_admin_principal(authorization: str | None) -> Principal:
    p = _decode_test_bearer(authorization)
    if p.role != "admin":
        raise HttpAuthError(403, "Admin role required")
    return p


def require_user_or_admin_status(authorization: str | None) -> Principal:
    p = _decode_test_bearer(authorization)
    if p.role not in ("user", "admin"):
        raise HttpAuthError(403, "Invalid token")
    return p


def bearer_token_for_user(*, sub: str, instagram_user_id: str) -> str:
    payload = {"role": "user", "sub": sub, "instagram_user_id": instagram_user_id}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return "Bearer " + base64.urlsafe_b64encode(raw).decode().rstrip("=")


def bearer_token_for_admin(*, sub: str) -> str:
    payload = {"role": "admin", "sub": sub}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return "Bearer " + base64.urlsafe_b64encode(raw).decode().rstrip("=")
