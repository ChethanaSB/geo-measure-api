import logging

import geopandas as gpd

logger = logging.getLogger(__name__)


def prepare_projected_geometries(gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoSeries, str]:
    """
    Ensure the geometry is in a projected Coordinate Reference System (CRS) suitable for measurements.
    
    Returns:
        tuple containing:
        - GeoSeries of the geometries in the projected CRS.
        - String representing the name or EPSG code of the measurement CRS used.
        
    Raises:
        ValueError if CRS is missing or transformation fails.
    """
    if gdf.crs is None:
        raise ValueError(
            "The uploaded file does not contain Coordinate Reference System (CRS) information. "
            "Cannot calculate accurate measurements without a known CRS."
        )

    if not gdf.crs.is_geographic:
        # Already projected (e.g., Web Mercator, existing UTM, State Plane)
        logger.info("CRS %s is already projected. Using directly for measurements.", gdf.crs)
        return gdf.geometry, gdf.crs.name or str(gdf.crs)

    # It's geographic (like EPSG:4326). We must project it to calculate area/length accurately.
    # We use UTM as it provides minimal distortion for localized datasets.
    try:
        # GeoPandas automatically calculates the centroid and determines the best UTM zone
        target_crs = gdf.estimate_utm_crs()
        logger.info(
            "Geographic CRS %s detected. Transforming to appropriate UTM zone: %s",
            gdf.crs, target_crs.name
        )
        
        projected_series = gdf.to_crs(target_crs).geometry
        return projected_series, target_crs.name
        
    except RuntimeError as exc:
        # estimate_utm_crs() can fail if the dataset crosses the anti-meridian or spans too broadly
        logger.error("Failed to determine UTM zone: %s", exc)
        raise ValueError(
            "Dataset spans too large of an area or crosses UTM bounds. "
            "Cannot safely select a single UTM zone for metric measurements."
        ) from exc
