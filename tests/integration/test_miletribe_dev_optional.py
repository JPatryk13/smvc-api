"""Optional live calls to MileTribe development API.

Set:

- ``SMVC_MILETRIBE_ACCESS_TOKEN`` -- manual JWT for the target user
- ``SMVC_MILETRIBE_TEST_VIDEO_PATH`` -- readable mp4 for upload
- ``SMVC_MILETRIBE_TEST_LOCATION`` -- location string accepted by ``POST /impressions/``

The test skips if any are missing.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from smvc_api.config import get_settings
from smvc_api.integrations.miletribe import MileTribeClient
from smvc_api.models.miletribe import PublishImpressionRequest

pytestmark = pytest.mark.integration


def _require_video_path() -> Path:
    raw = os.environ.get("SMVC_MILETRIBE_TEST_VIDEO_PATH")
    if not raw:
        pytest.skip("Set SMVC_MILETRIBE_TEST_VIDEO_PATH to a readable mp4 for live test")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"SMVC_MILETRIBE_TEST_VIDEO_PATH is not a file: {path}")
    return path


def _require_token() -> str:
    token = os.environ.get("SMVC_MILETRIBE_ACCESS_TOKEN")
    if not token:
        pytest.skip("Set SMVC_MILETRIBE_ACCESS_TOKEN for live MileTribe test")
    return token


def _require_location_string() -> str:
    """MileTribe requires a known location; use a valid value from your dev tenant."""
    loc = os.environ.get("SMVC_MILETRIBE_TEST_LOCATION")
    if not loc:
        pytest.skip(
            "Set SMVC_MILETRIBE_TEST_LOCATION to a location string accepted by POST /impressions/"
        )
    return loc


def test_upload_and_publish_impression_dev_api() -> None:
    settings = get_settings()
    token = _require_token()
    video_path = _require_video_path()
    location = _require_location_string()

    external_id = f"INSTAGRAM/poc-{uuid.uuid4().hex}"

    with MileTribeClient(
        base_url=settings.miletribe_base_url,
        access_token=token,
    ) as mt:
        video_bytes = video_path.read_bytes()
        uploaded = mt.upload_impression_video(video_bytes, filename=video_path.name)

        published = mt.publish_impression(
            PublishImpressionRequest(
                description="smvc-api skeleton integration test",
                location=location,
                is_public=False,
                impression_video_id=uploaded.impression_video_id,
                external_id=external_id,
            )
        )

    assert uploaded.impression_video_id
    assert published.id
