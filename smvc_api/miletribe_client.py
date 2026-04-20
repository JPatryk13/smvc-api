from __future__ import annotations

import json
from typing import Any

import httpx


class MileTribeClient:
    """HTTP client for MileTribe upload + publish ([U5], [U6])."""

    def __init__(self, base_url: str, access_token: str) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {access_token}"}

    async def upload_impression_video(
        self, video_bytes: bytes, filename: str = "video.mp4"
    ) -> dict[str, Any]:
        """POST /impression-videos/ with multipart field `video` per OpenAPI."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"video": (filename, video_bytes, "video/mp4")}
            r = await client.post(
                f"{self._base}/impression-videos/",
                headers=self._headers,
                files=files,
            )
            return _handle_json_response(r)

    async def publish_impression(self, body: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {k: v for k, v in body.items() if v is not None}
            r = await client.post(
                f"{self._base}/impressions/",
                headers={**self._headers, "Content-Type": "application/json"},
                content=json.dumps(payload),
            )
            return _handle_json_response(r)


def _handle_json_response(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 409:
        try:
            return response.json() if response.content else {"duplicate": True}
        except json.JSONDecodeError:
            return {"duplicate": True, "status_code": 409}
    response.raise_for_status()
    if not response.content:
        return {}
    return response.json()
