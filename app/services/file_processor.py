import logging
from pathlib import Path
from typing import Any

import geopandas as gpd

logger = logging.getLogger(__name__)


def process_kml(file_path: Path) -> dict[str, Any]:
    """
    Read a KML file, extract its features, and return a structured dictionary.
    
    Uses GeoPandas with the pyogrio engine to parse the KML natively.
    """
    logger.info("Processing KML file: %s", file_path)

    try:
        # Note: KML driver is supported by GDAL/pyogrio natively.
        gdf = gpd.read_file(file_path, engine="pyogrio")
    except Exception as exc:
        logger.error("Failed to read KML file: %s", exc)
        raise ValueError(f"Failed to parse KML file: {str(exc)}")

    # Extract CRS if available, else default to None
    crs = str(gdf.crs) if gdf.crs else None

    features = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        # If geometry is null/empty for some reason, we handle it gracefully
        if geom is None or geom.is_empty:
            geom_type = "None"
            geometry_json = None
        else:
            geom_type = geom.geom_type
            # Extract basic GeoJSON-like representation (useful for APIs)
            geometry_json = geom.__geo_interface__

        # Properties: everything except the geometry column
        properties = {
            col: row[col]
            for col in gdf.columns
            if col != "geometry" and (not isinstance(row[col], float) or row[col] == row[col])
        }

        import pandas as pd
        import math
        
        clean_properties = {}
        for k, v in properties.items():
            if pd.isna(v):
                clean_properties[k] = None
            elif hasattr(v, "item"):  # Convert numpy types to native Python types
                clean_properties[k] = v.item()
            else:
                clean_properties[k] = v

        feature = {
            "feature_id": str(idx),
            "geometry_type": geom_type,
            "geometry": geometry_json,
            "crs": crs,
            "properties": clean_properties,
            # We will populate these in later milestones
            "measurement": None,
            "measurement_status": "PENDING",
        }
        features.append(feature)

    result = {
        "feature_count": len(features),
        "crs": crs,
        "features": features
    }
    
    import json
    
    # Handle any remaining numpy/shapely types safely
    class SafeEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, "item"):
                return obj.item()
            if hasattr(obj, "__geo_interface__"):
                return obj.__geo_interface__
            return str(obj)

    safe_result = json.loads(json.dumps(result, cls=SafeEncoder))
    
    logger.info("Successfully extracted %d features from KML", len(features))
    return safe_result
