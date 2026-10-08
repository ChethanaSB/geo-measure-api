"""Tests for CRS detection and UTM projection logic."""
import pytest
import geopandas as gpd
from shapely.geometry import Polygon

from app.services.crs import prepare_projected_geometries


class TestCRSService:
    def test_geographic_crs_gets_projected(self):
        """EPSG:4326 (geographic) must be projected to a UTM zone."""
        poly = Polygon([(-122.4, 37.8), (-122.3, 37.8), (-122.3, 37.9), (-122.4, 37.9), (-122.4, 37.8)])
        gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")

        projected_geoms, crs_name = prepare_projected_geometries(gdf)

        assert "UTM" in crs_name
        # In a projected CRS, area should be much larger than in degrees
        assert projected_geoms.iloc[0].area > 1.0

    def test_already_projected_crs_used_directly(self):
        """If data is already in a projected CRS, it should be used without transformation."""
        poly = Polygon([(500000, 4200000), (501000, 4200000), (501000, 4201000), (500000, 4201000), (500000, 4200000)])
        gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:32610")  # WGS84 / UTM Zone 10N

        projected_geoms, crs_name = prepare_projected_geometries(gdf)

        assert projected_geoms.iloc[0].area == pytest.approx(1_000_000, rel=0.01)

    def test_missing_crs_raises_value_error(self):
        """A GeoDataFrame without a CRS must raise a ValueError."""
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        gdf = gpd.GeoDataFrame(geometry=[poly])  # No CRS

        with pytest.raises(ValueError, match="CRS"):
            prepare_projected_geometries(gdf)
