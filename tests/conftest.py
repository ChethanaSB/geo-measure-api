"""
Shared pytest fixtures used across all test modules.
"""
import os
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Point, Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# In-memory test database — isolated from the real geo_measure.db
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_geo_measure.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient with a temporary in-memory SQLite DB."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as c:
        yield c

    # Cleanup test DB file after session
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    test_db_path = Path("test_geo_measure.db")
    try:
        if test_db_path.exists():
            test_db_path.unlink()
    except PermissionError:
        pass  # Windows may hold the file; acceptable for test cleanup


@pytest.fixture()
def sample_kml_path(tmp_path: Path) -> Path:
    """Write a minimal KML with Polygon, LineString, and Point to a temp file."""
    kml_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Site A</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -122.366278,37.818844,0
              -122.365248,37.819267,0
              -122.365640,37.819861,0
              -122.366669,37.819429,0
              -122.366278,37.818844,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>Path B</name>
      <LineString>
        <coordinates>
          -122.366278,37.818844,0
          -122.365248,37.819267,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Point C</name>
      <Point>
        <coordinates>-122.366278,37.818844,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(kml_content, encoding="utf-8")
    return kml_file


@pytest.fixture()
def sample_zip_path(tmp_path: Path) -> Path:
    """Create a ZIP containing a minimal Shapefile (Polygon only)."""
    poly = Polygon([
        (-122.366278, 37.818844),
        (-122.365248, 37.819267),
        (-122.365640, 37.819861),
        (-122.366669, 37.819429),
        (-122.366278, 37.818844),
    ])
    gdf = gpd.GeoDataFrame({"name": ["Test Polygon"]}, geometry=[poly], crs="EPSG:4326")

    shp_dir = tmp_path / "shp"
    shp_dir.mkdir()
    gdf.to_file(shp_dir / "sample.shp", engine="pyogrio")

    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in shp_dir.iterdir():
            zf.write(f, arcname=f.name)

    return zip_path
