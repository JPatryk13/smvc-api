import pytest
from starlette.testclient import TestClient

from smvc_api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
