"""Tests for the GET /api/files/{id}/ and GET /api/files/{id}/measurements/ endpoints."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def upload_kml(client: TestClient, kml_path: Path) -> str:
    """Helper to upload a KML file and return its file_id."""
    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    assert response.status_code == 201
    return response.json()["id"]


class TestGetFileInfo:
    def test_get_existing_file_returns_200(self, client: TestClient, sample_kml_path: Path):
        file_id = upload_kml(client, sample_kml_path)
        response = client.get(f"/api/files/{file_id}/")
        assert response.status_code == 200

    def test_get_file_info_structure(self, client: TestClient, sample_kml_path: Path):
        """GET /api/files/{id}/ must return all metadata fields."""
        file_id = upload_kml(client, sample_kml_path)
        data = client.get(f"/api/files/{file_id}/").json()

        assert data["id"] == file_id
        assert data["filename"] == "sample.kml"
        assert data["status"] == "COMPLETED"
        assert data["feature_count"] == 3
        assert data["crs"] is not None
        assert data["measurement_crs"] is not None
        assert data["created_at"] is not None

    def test_get_unknown_file_returns_404(self, client: TestClient):
        response = client.get("/api/files/doesnotexist123/")
        assert response.status_code == 404

    def test_get_file_does_not_expose_measurements(self, client: TestClient, sample_kml_path: Path):
        """The file info endpoint must NOT include the full features array."""
        file_id = upload_kml(client, sample_kml_path)
        data = client.get(f"/api/files/{file_id}/").json()
        assert "features" not in data


class TestGetMeasurements:
    def test_get_measurements_returns_200(self, client: TestClient, sample_kml_path: Path):
        file_id = upload_kml(client, sample_kml_path)
        response = client.get(f"/api/files/{file_id}/measurements/")
        assert response.status_code == 200

    def test_measurements_response_structure(self, client: TestClient, sample_kml_path: Path):
        """GET measurements must return the features array with measurements."""
        file_id = upload_kml(client, sample_kml_path)
        data = client.get(f"/api/files/{file_id}/measurements/").json()

        assert data["file_id"] == file_id
        assert "features" in data
        assert len(data["features"]) == 3
        assert data["crs"] is not None
        assert data["measurement_crs"] is not None

    def test_measurements_unknown_file_returns_404(self, client: TestClient):
        response = client.get("/api/files/unknown999/measurements/")
        assert response.status_code == 404

    def test_health_endpoint(self, client: TestClient):
        """Health check must return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
