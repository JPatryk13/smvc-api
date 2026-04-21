"""Pipeline request and response shapes (bridge plan)."""

from pydantic import BaseModel, Field


class PipelineSummary(BaseModel):
    """Returned by user sync and admin pipeline runs."""

    processed: int = 0
    skipped: int = 0
    failed: int = 0
    external_ids: list[str] = Field(default_factory=list)


class AdminPipelineRunRequest(BaseModel):
    """POST /admin/v1/pipeline/run body."""

    source_instagram_account_id: str = Field(min_length=1)
    target_miletribe_user_id: str = Field(min_length=1)
    miletribe_access_token: str | None = None
