import json
import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


def _extract_features(gdf: gpd.GeoDataFrame) -> dict[str, Any]:
    """Helper to extract features from a GeoDataFrame into the required JSON structure."""
    crs = str(gdf.crs) if gdf.crs else None
    features = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if geom is None or geom.is_empty:
            geom_type = "None"
            geometry_json = None
        else:
            geom_type = geom.geom_type
            geometry_json = geom.__geo_interface__

        properties = {
            col: row[col]
            for col in gdf.columns
            if col != "geometry" and (not isinstance(row[col], float) or row[col] == row[col])
        }
        
        clean_properties = {}
        for k, v in properties.items():
            if pd.isna(v):
                clean_properties[k] = None
            elif hasattr(v, "item"):
                clean_properties[k] = v.item()
            else:
                clean_properties[k] = v

        feature = {
            "feature_id": str(idx),
            "geometry_type": geom_type,
            "geometry": geometry_json,
            "crs": crs,
            "properties": clean_properties,
            "measurement": None,
            "measurement_status": "PENDING",
        }
        features.append(feature)

    result = {
        "feature_count": len(features),
        "crs": crs,
        "features": features
    }
    
    class SafeEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, "item"):
                return obj.item()
            if hasattr(obj, "__geo_interface__"):
                return obj.__geo_interface__
            return str(obj)

    safe_result = json.loads(json.dumps(result, cls=SafeEncoder))
    return safe_result


def process_kml(file_path: Path) -> dict[str, Any]:
    """Read a KML file, extract its features, and return a structured dictionary."""
    logger.info("Processing KML file: %s", file_path)

    try:
        gdf = gpd.read_file(file_path, engine="pyogrio")
    except Exception as exc:
        logger.error("Failed to read KML file: %s", exc)
        raise ValueError(f"Failed to parse KML file: {str(exc)}")

    result = _extract_features(gdf)
    logger.info("Successfully extracted %d features from KML", result["feature_count"])
    return result


def process_shapefile(shp_path: Path) -> dict[str, Any]:
    """Read a Shapefile, extract its features, and return a structured dictionary."""
    logger.info("Processing Shapefile: %s", shp_path)

    try:
        gdf = gpd.read_file(shp_path, engine="pyogrio")
    except Exception as exc:
        logger.error("Failed to read Shapefile: %s", exc)
        raise ValueError(f"Failed to parse Shapefile: {str(exc)}")

    result = _extract_features(gdf)
    logger.info("Successfully extracted %d features from Shapefile", result["feature_count"])
    return result
