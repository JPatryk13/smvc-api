"""Unit tests for MileTribe HTTP client (mocked transport)."""

import io
import json

import httpx
import pytest

from smvc_api.integrations.miletribe import MileTribeClient
from smvc_api.models.miletribe import PublishImpressionRequest


def test_upload_impression_video_posts_multipart_and_parses_response() -> None:
    body = (
        b'{"impression_video_id":"vid1","video_file_url":"https://x/v.mp4",'
        b'"thumbnail_file_url":"https://x/t.jpg","created_at":"2024-01-01T00:00:00Z",'
        b'"published":false,"sec_length":12}'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/impression-videos/"
        assert request.headers["Authorization"] == "Bearer tok"
        assert "multipart/form-data" in request.headers["Content-Type"]
        assert b'name="video"' in request.content
        return httpx.Response(201, content=body)

    transport = httpx.MockTransport(handler)
    raw = httpx.Client(
        transport=transport,
        base_url="https://mt.example",
        headers={"Authorization": "Bearer tok", "Accept": "application/json"},
    )
    try:
        client = MileTribeClient(
            base_url="https://mt.example",
            access_token="tok",
            http_client=raw,
        )
        result = client.upload_impression_video(b"\x00\x01", filename="a.mp4")
    finally:
        raw.close()

    assert result.impression_video_id == "vid1"
    assert result.sec_length == 12


def test_publish_impression_posts_json_and_parses_response() -> None:
    body = b'{"id":"imp1","description":"hi","external_id":"INSTAGRAM/x"}'

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/impressions/"
        assert request.headers["Authorization"] == "Bearer tok"
        assert request.headers["Content-Type"].startswith("application/json")
        payload = json.loads(request.content.decode())
        assert payload["description"] == "d"
        assert payload["location"] == "loc"
        assert payload["is_public"] is True
        return httpx.Response(201, content=body)

    transport = httpx.MockTransport(handler)
    raw = httpx.Client(
        transport=transport,
        base_url="https://mt.example",
        headers={"Authorization": "Bearer tok", "Accept": "application/json"},
    )
    try:
        client = MileTribeClient(
            base_url="https://mt.example",
            access_token="tok",
            http_client=raw,
        )
        result = client.publish_impression(
            PublishImpressionRequest(
                description="d",
                location="loc",
                is_public=True,
                impression_video_id="vid1",
                external_id="INSTAGRAM/x",
            )
        )
    finally:
        raw.close()

    assert result.id == "imp1"
    assert result.external_id == "INSTAGRAM/x"


def test_upload_raises_on_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "nope"})

    transport = httpx.MockTransport(handler)
    raw = httpx.Client(
        transport=transport,
        base_url="https://mt.example",
        headers={"Authorization": "Bearer tok", "Accept": "application/json"},
    )
    try:
        client = MileTribeClient(
            base_url="https://mt.example",
            access_token="tok",
            http_client=raw,
        )
        with pytest.raises(httpx.HTTPStatusError):
            client.upload_impression_video(io.BytesIO(b"x"), filename="a.mp4")
    finally:
        raw.close()
