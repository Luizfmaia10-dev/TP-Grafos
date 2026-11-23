from fastapi.testclient import TestClient

from app import main


def test_geocoding_config_uses_environment_key(monkeypatch, tmp_path):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")
    monkeypatch.setattr(main, "LOCAL_ENV_FILE", tmp_path / ".env.local", raising=False)

    response = TestClient(main.create_app()).get("/config/geocoding")

    assert response.status_code == 200
    assert response.json() == {"api_key": "test-key", "available": True}


def test_geocoding_config_reports_unavailable_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    monkeypatch.setattr(main, "LOCAL_ENV_FILE", tmp_path / ".env.local", raising=False)

    response = TestClient(main.create_app()).get("/config/geocoding")

    assert response.status_code == 200
    assert response.json() == {"api_key": None, "available": False}


def test_geocoding_config_reads_ignored_local_file(monkeypatch, tmp_path):
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    local_file = tmp_path / ".env.local"
    local_file.write_text(
        "UNRELATED=value\nGEOAPIFY_API_KEY=local-key\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "LOCAL_ENV_FILE", local_file, raising=False)

    response = TestClient(main.create_app()).get("/config/geocoding")

    assert response.json() == {"api_key": "local-key", "available": True}
