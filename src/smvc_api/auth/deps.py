"""HTTP dependencies for user Bearer vs admin API key."""

from typing import Annotated

from fastapi import Header, HTTPException, status

from smvc_api.config import get_settings


def require_user_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.user_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def require_admin_api_key(
    x_admin_api_key: Annotated[str | None, Header(alias="X-Admin-API-Key")] = None,
) -> None:
    settings = get_settings()
    key = settings.admin_api_key
    if key is None or not str(key).strip():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if x_admin_api_key != key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
