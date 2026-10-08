"""Tests for Shapefile ZIP upload processing."""
import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon


class TestShapefileUpload:
    def test_valid_zip_returns_201(self, client: TestClient, sample_zip_path: Path):
        """A valid ZIP containing a Shapefile should return 201."""
        with open(sample_zip_path, "rb") as f:
            response = client.post("/api/files/", files={"file": ("sample.zip", f, "application/zip")})
        assert response.status_code == 201

    def test_valid_zip_response_structure(self, client: TestClient, sample_zip_path: Path):
        """Response for a Shapefile ZIP must include all required fields."""
        with open(sample_zip_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.zip", f, "application/zip")}).json()

        assert data["status"] == "COMPLETED"
        assert data["file_type"] == "zip"
        assert data["feature_count"] >= 1
        assert data["crs"] is not None
        assert data["measurement_crs"] is not None
        assert len(data["features"]) >= 1

    def test_shapefile_polygon_area_in_metres(self, client: TestClient, sample_zip_path: Path):
        """Shapefile polygon area must be in square metres (positive, greater than 1.0)."""
        with open(sample_zip_path, "rb") as f:
            data = client.post("/api/files/", files={"file": ("sample.zip", f, "application/zip")}).json()

        polygon = next(f for f in data["features"] if f["geometry_type"] == "Polygon")
        assert polygon["measurement"] > 1.0
        assert polygon["unit"] == "m²"

    def test_zip_without_shp_returns_400(self, client: TestClient, tmp_path: Path):
        """A ZIP that doesn't contain a .shp file must return 400."""
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("readme.txt", "No shapefile here")
        with open(bad_zip, "rb") as f:
            response = client.post("/api/files/", files={"file": ("bad.zip", f, "application/zip")})
        assert response.status_code == 400
        assert ".shp" in response.json()["detail"]

    def test_zip_path_traversal_rejected(self, client: TestClient, tmp_path: Path):
        """A ZIP with path traversal entries must be rejected with 400."""
        bad_zip = tmp_path / "traversal.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("../../evil.shp", "malicious content")
        with open(bad_zip, "rb") as f:
            response = client.post("/api/files/", files={"file": ("traversal.zip", f, "application/zip")})
        assert response.status_code == 400
        assert "traversal" in response.json()["detail"].lower()
