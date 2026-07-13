"""
API tests.

Note: we mock `predict` rather than actually running the model. This keeps
tests fast and means CI doesn't need to download ~14MB of model weights on
every run. Testing your API layer separately from your model logic is a
useful habit generally, not just a speed hack.
"""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _sample_image_bytes() -> bytes:
    image = Image.new("RGB", (64, 64), color="blue")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.predict")
def test_predict_returns_top_predictions(mock_predict):
    mock_predict.return_value = [
        ("golden retriever", 0.91),
        ("labrador retriever", 0.05),
        ("beagle", 0.02),
    ]

    response = client.post(
        "/predict",
        files={"file": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["predictions"][0]["label"] == "golden retriever"
    assert len(body["predictions"]) == 3


def test_predict_rejects_unsupported_content_type():
    response = client.post(
        "/predict",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400


def test_predict_rejects_empty_file():
    response = client.post(
        "/predict",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
