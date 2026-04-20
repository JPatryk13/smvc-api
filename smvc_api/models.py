from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TransferStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    completed_with_errors = "completed_with_errors"
    failed = "failed"


@dataclass
class TransferPhaseCounts:
    discovered: int = 0
    scenery_selected: int = 0
    uploaded: int = 0
    failed: int = 0


@dataclass
class TransferStatusResponse:
    transfer_id: str
    status: TransferStatus
    counts: TransferPhaseCounts = field(default_factory=TransferPhaseCounts)
    errors: list[str] = field(default_factory=list)


@dataclass
class UserTransferRequest:
    instagram_user_id: str | None = None


@dataclass
class AdminTransferRequest:
    source_instagram_user_id: str
    target_miletribe_user_id: str


@dataclass
class TransferAcceptedResponse:
    transfer_id: str


@dataclass
class ClassificationResult:
    """Output per [M2] / [M3]."""

    score: float
    label: str
    is_scenery_only: bool
    explanation: str | None = None
