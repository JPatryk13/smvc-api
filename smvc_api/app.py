from __future__ import annotations

import json
from typing import Any

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from smvc_api.auth import (
    HttpAuthError,
    require_admin_principal,
    require_user_or_admin_status,
    require_user_principal,
)
from smvc_api.models import AdminTransferRequest, UserTransferRequest


def _store():
    from smvc_api.store import TransferStore

    if not hasattr(app.state, "transfer_store"):
        app.state.transfer_store = TransferStore()
    return app.state.transfer_store


def _audit():
    from smvc_api.store import AuditLog

    if not hasattr(app.state, "audit_log"):
        app.state.audit_log = AuditLog()
    return app.state.audit_log


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def create_user_transfer(request: Request) -> Response:
    """[U1][U3] User-only transfer."""
    try:
        principal = require_user_principal(request.headers.get("authorization"))
    except HttpAuthError as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)

    body_raw: dict[str, Any] = {}
    if request.method == "POST" and request.headers.get("content-length", "0") != "0":
        try:
            body_raw = await request.json()
        except json.JSONDecodeError:
            body_raw = {}
    body = UserTransferRequest(instagram_user_id=body_raw.get("instagram_user_id"))

    if body.instagram_user_id and body.instagram_user_id != principal.instagram_user_id:
        return JSONResponse(
            {"detail": "Cannot transfer for another Instagram account"}, status_code=403
        )

    store = _store()
    ts = store.create()
    return JSONResponse({"transfer_id": ts.transfer_id}, status_code=202)


async def create_admin_transfer(request: Request) -> Response:
    """[A1][A2][A3] Admin cross-account transfer."""
    try:
        principal = require_admin_principal(request.headers.get("authorization"))
    except HttpAuthError as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)

    try:
        raw = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"detail": "Invalid JSON"}, status_code=422)

    try:
        body = AdminTransferRequest(
            source_instagram_user_id=raw["source_instagram_user_id"],
            target_miletribe_user_id=raw["target_miletribe_user_id"],
        )
    except KeyError:
        return JSONResponse({"detail": "Missing required fields"}, status_code=422)

    store = _store()
    audit = _audit()
    ts = store.create()
    audit.admin_transfer(
        admin_sub=principal.subject,
        source_instagram_user_id=body.source_instagram_user_id,
        target_miletribe_user_id=body.target_miletribe_user_id,
        transfer_id=ts.transfer_id,
    )
    return JSONResponse({"transfer_id": ts.transfer_id}, status_code=202)


async def get_transfer_status(request: Request) -> Response:
    """[O1] Status resource."""
    try:
        require_user_or_admin_status(request.headers.get("authorization"))
    except HttpAuthError as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)

    tid = request.path_params["transfer_id"]
    row = _store().get(tid)
    if not row:
        raise HTTPException(404, "Unknown transfer_id")

    def serialize_counts(c: Any) -> dict[str, Any]:
        return {
            "discovered": c.discovered,
            "scenery_selected": c.scenery_selected,
            "uploaded": c.uploaded,
            "failed": c.failed,
        }

    payload = {
        "transfer_id": row.transfer_id,
        "status": row.status.value,
        "counts": serialize_counts(row.counts),
        "errors": row.errors,
    }
    return JSONResponse(payload)


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


routes = [
    Route("/health", endpoint=health, methods=["GET"]),
    Route("/v1/transfers", endpoint=create_user_transfer, methods=["POST"]),
    Route("/v1/admin/transfers", endpoint=create_admin_transfer, methods=["POST"]),
    Route("/v1/transfers/{transfer_id}", endpoint=get_transfer_status, methods=["GET"]),
]

app = Starlette(
    routes=routes, exception_handlers={HTTPException: http_exception_handler}
)
