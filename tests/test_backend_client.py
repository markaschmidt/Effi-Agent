from __future__ import annotations

from backend import BackendClient


def test_client_uses_backend_paths() -> None:
    client = BackendClient("http://127.0.0.1:8000/", api_key="test-key")
    assert str(client._http.base_url).rstrip("/") == "http://127.0.0.1:8000"
    assert client._http.headers["X-API-Key"] == "test-key"
    assert hasattr(client, "upload_recording")
