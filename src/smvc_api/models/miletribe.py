"""DTOs aligned with MileTribe OpenAPI (subset used by smvc-api)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImpressionVideoResponse(BaseModel):
    """Response from POST /impression-videos/."""

    impression_video_id: str
    video_file_url: str
    thumbnail_file_url: str
    created_at: datetime
    published: bool
    sec_length: int


class PublishImpressionRequest(BaseModel):
    """Body for POST /impressions/."""

    description: str
    location: str
    is_public: bool
    impression_video_id: str | None = None
    external_id: str | None = None


class PublishedLocationImpression(BaseModel):
    """Subset of POST /impressions/ response fields we rely on."""

    model_config = ConfigDict(extra="ignore")

    id: str
    description: str | None = None
    external_id: str | None = None
