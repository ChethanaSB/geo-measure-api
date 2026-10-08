"""Tests for the file upload endpoint — validation and happy paths."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestUploadValidation:
    def test_upload_missing_file_returns_422(self, client: TestClient):
        """Sending no file should return 422 Unprocessable Entity."""
        response = client.post("/api/files/")
        assert response.status_code == 422

    def test_upload_unsupported_extension_returns_400(self, client: TestClient, tmp_path: Path):
        """Uploading a .txt file should be rejected with 400."""
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("not a geospatial file")
        with open(txt_file, "rb") as f:
            response = client.post("/api/files/", files={"file": ("notes.txt", f, "text/plain")})
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_empty_file_returns_400(self, client: TestClient, tmp_path: Path):
        """Uploading an empty .kml file should be rejected with 400."""
        empty = tmp_path / "empty.kml"
        empty.write_bytes(b"")
        with open(empty, "rb") as f:
            response = client.post("/api/files/", files={"file": ("empty.kml", f, "application/vnd.google-earth.kml+xml")})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


class TestKMLUpload:
    def test_valid_kml_returns_201(self, client: TestClient, sample_kml_path: Path):
        """A valid KML file should be accepted and return 201."""
        with open(sample_kml_path, "rb") as f:
            response = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")})
        assert response.status_code == 201

    def test_valid_kml_response_structure(self, client: TestClient, sample_kml_path: Path):
        """Response must contain all required fields."""
        with open(sample_kml_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}).json()

        assert "id" in data
        assert data["filename"] == "sample.kml"
        assert data["file_type"] == "kml"
        assert data["status"] == "COMPLETED"
        assert data["feature_count"] == 3
        assert data["crs"] is not None
        assert data["measurement_crs"] is not None

    def test_kml_features_have_required_fields(self, client: TestClient, sample_kml_path: Path):
        """Each feature must include feature_id, geometry_type, geometry, crs, properties."""
        with open(sample_kml_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}).json()

        assert len(data["features"]) == 3
        for feature in data["features"]:
            assert "feature_id" in feature
            assert "geometry_type" in feature
            assert "geometry" in feature
            assert "crs" in feature
            assert "properties" in feature
            assert "measurement" in feature
            assert "measurement_status" in feature

    def test_kml_polygon_area_is_positive(self, client: TestClient, sample_kml_path: Path):
        """Polygon area must be a positive number (m²)."""
        with open(sample_kml_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}).json()

        polygon = next(f for f in data["features"] if f["geometry_type"] == "Polygon")
        assert polygon["measurement"] is not None
        assert polygon["measurement"] > 0
        assert polygon["unit"] == "m²"
        assert polygon["measurement_status"] == "COMPLETED"

    def test_kml_linestring_length_is_positive(self, client: TestClient, sample_kml_path: Path):
        """LineString length must be a positive number (m)."""
        with open(sample_kml_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}).json()

        line = next(f for f in data["features"] if f["geometry_type"] == "LineString")
        assert line["measurement"] is not None
        assert line["measurement"] > 0
        assert line["unit"] == "m"
        assert line["measurement_status"] == "COMPLETED"

    def test_kml_point_has_no_measurement(self, client: TestClient, sample_kml_path: Path):
        """Point features must not produce a measurement."""
        with open(sample_kml_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}).json()

        point = next(f for f in data["features"] if f["geometry_type"] == "Point")
        assert point["measurement"] is None
        assert point["measurement_status"] == "NOT_REQUIRED"
