import json

from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock import mocker

from app.main import app

client = TestClient(app, base_url="http://localhost:8000/api/v1/")


def test_request_not_made_by_twillio():
    data = {"number": 374, "message": "test"}
    response = client.post("bots/receive-message", data=json.dumps(data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
