"""MileTribe REST client (OAuth2 bearer as published in OpenAPI)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import IO

import httpx

from smvc_api.models.miletribe import (
    ImpressionVideoResponse,
    PublishImpressionRequest,
    PublishedLocationImpression,
)

logger = logging.getLogger(__name__)


class MileTribeClient:
    """Sync HTTP client for upload + publish flows against MileTribe API."""

    def __init__(
        self,
        *,
        base_url: str,
        access_token: str,
        timeout_s: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=timeout_s,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> MileTribeClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def upload_impression_video(
        self,
        video: bytes | IO[bytes],
        *,
        filename: str = "upload.mp4",
        content_type: str = "video/mp4",
        extra_headers: Mapping[str, str] | None = None,
    ) -> ImpressionVideoResponse:
        """POST /impression-videos/ (multipart field name ``video``)."""
        headers = dict(extra_headers) if extra_headers else None
        files = {"video": (filename, video, content_type)}
        response = self._client.post("/impression-videos/", files=files, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(
            "MileTribe upload impression video ok impression_video_id=%s",
            data.get("impression_video_id"),
        )
        return ImpressionVideoResponse.model_validate(data)

    def publish_impression(
        self,
        body: PublishImpressionRequest,
        *,
        extra_headers: Mapping[str, str] | None = None,
    ) -> PublishedLocationImpression:
        """POST /impressions/."""
        headers = dict(extra_headers) if extra_headers else None
        response = self._client.post(
            "/impressions/",
            json=body.model_dump(exclude_none=True),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        logger.info("MileTribe publish impression ok id=%s", data.get("id"))
        return PublishedLocationImpression.model_validate(data)
