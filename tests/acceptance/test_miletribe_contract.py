"""Contract tests against MileTribe-shaped HTTP. Docstrings quote criteria from tests/acceptance/REQUIREMENTS.md."""

import json
from typing import Any

import httpx
import pytest
import respx

from smvc_api.miletribe_client import MileTribeClient


@pytest.mark.asyncio
@respx.mock
async def test_upload_uses_multipart_field_video(respx_mock: Any) -> None:
    """**U5** — For each selected clip, upload via MileTribe **`POST /impression-videos/`**; one clip failing should not necessarily kill the whole batch (**N3**). Retries/backoff belong here."""

    # Given a mocked MileTribe upload endpoint that returns 201 JSON.
    route = respx_mock.post("https://mt.example/impression-videos/").mock(
        return_value=httpx.Response(
            201,
            json={
                "impression_video_id": "vid-1",
                "video_file_url": "https://example/v.mp4",
                "thumbnail_file_url": "https://example/t.jpg",
                "created_at": "2026-01-01T00:00:00Z",
                "published": False,
                "sec_length": 12,
            },
        )
    )

    # When the client uploads bytes as a video file.
    client = MileTribeClient("https://mt.example", "token")
    await client.upload_impression_video(
        b"\x00\x00\x00\x18ftypmp42", filename="clip.mp4"
    )

    # Then the request is multipart with a part named "video".
    assert route.called
    req = route.calls[0].request
    assert "multipart/form-data" in req.headers.get("content-type", "")
    body = req.content
    assert b'name="video"' in body


@pytest.mark.asyncio
@respx.mock
async def test_publish_impression_json_shape(respx_mock: Any) -> None:
    """**U6** — Publish with **`external_id`**; if MileTribe returns **409** for a duplicate of the same logical impression, treat it as **success** for idempotency."""

    # Given a mocked impressions endpoint that accepts POST and returns 201.
    recorded = respx_mock.post("https://mt.example/impressions/").mock(
        return_value=httpx.Response(
            201,
            json={"id": "imp-1"},
        )
    )

    # When publishing an impression with MileTribe-required fields and external_id.
    client = MileTribeClient("https://mt.example", "token")
    body = {
        "description": "Coast",
        "location": "uuid-or-slug",
        "is_public": True,
        "impression_video_id": "vid-1",
        "external_id": "INSTAGRAM/17841405309211844",
    }
    await client.publish_impression(body)

    # Then the JSON body uses Bearer auth and preserves description and external_id.
    assert recorded.called
    req = recorded.calls[0].request
    assert req.headers.get("authorization") == "Bearer token"
    parsed = json.loads(req.content.decode())
    assert parsed["description"] == "Coast"
    assert parsed["external_id"] == "INSTAGRAM/17841405309211844"


@pytest.mark.asyncio
@respx.mock
async def test_publish_409_idempotent_success(respx_mock: Any) -> None:
    """**U6** — Publish with **`external_id`**; if MileTribe returns **409** for a duplicate of the same logical impression, treat it as **success** for idempotency."""

    # Given MileTribe responds 409 duplicate for the publish call.
    respx_mock.post("https://mt.example/impressions/").mock(
        return_value=httpx.Response(409, json={"detail": "duplicate"})
    )

    # When publishing with a stable external_id (retry / idempotent case).
    client = MileTribeClient("https://mt.example", "token")
    out = await client.publish_impression(
        {
            "description": "x",
            "location": "y",
            "is_public": False,
            "external_id": "INSTAGRAM/1",
        }
    )

    # Then the client surfaces the response without raising (treat duplicate as handled).
    assert out.get("detail") == "duplicate"


@pytest.mark.asyncio
@respx.mock
async def test_upload_401_surfaces(respx_mock: Any) -> None:
    """**MileTribe contract** (hard constraint) — Follow their OpenAPI: **`multipart/form-data`** with field **`video`**, JSON for impressions, stable **`external_id`**, and correct handling of **401**, **422**, **409**."""

    # Given MileTribe rejects the upload with 401 Unauthorized.
    respx_mock.post("https://mt.example/impression-videos/").mock(
        return_value=httpx.Response(401)
    )

    # When the client uploads with an invalid token.
    client = MileTribeClient("https://mt.example", "bad")

    # Then httpx raises HTTPStatusError (failure is not silently ignored).
    with pytest.raises(httpx.HTTPStatusError):
        await client.upload_impression_video(b"x")
