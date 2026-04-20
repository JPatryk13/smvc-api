from __future__ import annotations

import itertools
import threading
from datetime import UTC, datetime

from smvc_api.models import TransferPhaseCounts, TransferStatus, TransferStatusResponse


class TransferStore:
    """In-memory transfer registry for API acceptance ([O1]); replace with DB in production."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._transfers: dict[str, TransferStatusResponse] = {}
        self._seq = itertools.count(1)

    def create(self) -> TransferStatusResponse:
        with self._lock:
            tid = f"t-{next(self._seq)}"
            ts = TransferStatusResponse(transfer_id=tid, status=TransferStatus.queued)
            self._transfers[tid] = ts
            return ts

    def mark_running(self, transfer_id: str) -> None:
        self._patch(transfer_id, status=TransferStatus.running)

    def complete_ok(self, transfer_id: str, counts: TransferPhaseCounts) -> None:
        self._patch(transfer_id, status=TransferStatus.completed, counts=counts)

    def complete_partial(
        self, transfer_id: str, counts: TransferPhaseCounts, errors: list[str]
    ) -> None:
        self._patch(
            transfer_id,
            status=TransferStatus.completed_with_errors,
            counts=counts,
            errors=errors,
        )

    def fail(self, transfer_id: str, message: str) -> None:
        self._patch(transfer_id, status=TransferStatus.failed, errors=[message])

    def get(self, transfer_id: str) -> TransferStatusResponse | None:
        with self._lock:
            return self._transfers.get(transfer_id)

    def _patch(
        self,
        transfer_id: str,
        *,
        status: TransferStatus | None = None,
        counts: TransferPhaseCounts | None = None,
        errors: list[str] | None = None,
    ) -> None:
        with self._lock:
            cur = self._transfers.get(transfer_id)
            if not cur:
                return
            if status is not None:
                cur.status = status
            if counts is not None:
                cur.counts = counts
            if errors is not None:
                cur.errors = errors


class AuditLog:
    """Minimal audit trail for [A3]."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[dict[str, object]] = []

    def admin_transfer(
        self,
        *,
        admin_sub: str,
        source_instagram_user_id: str,
        target_miletribe_user_id: str,
        transfer_id: str,
    ) -> None:
        entry: dict[str, object] = {
            "at": datetime.now(UTC).isoformat(),
            "admin_subject": admin_sub,
            "source_instagram_user_id": source_instagram_user_id,
            "target_miletribe_user_id": target_miletribe_user_id,
            "transfer_id": transfer_id,
        }
        with self._lock:
            self._entries.append(entry)

    def entries(self) -> tuple[dict[str, object], ...]:
        with self._lock:
            return tuple(self._entries)
