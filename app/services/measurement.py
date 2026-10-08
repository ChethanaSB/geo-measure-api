from typing import Any

from shapely.geometry.base import BaseGeometry


def calculate_measurement(geom: BaseGeometry | None, geom_type: str) -> dict[str, Any]:
    """
    Calculate the appropriate measurement for a given geometry type.
    
    Currently performs calculations on the raw geometry.
    CRS transformation to projected coordinates (metres) will be added in Milestone 6.
    """
    if geom is None or geom.is_empty:
        return {
            "measurement": None,
            "unit": None,
            "measurement_status": "UNSUPPORTED"
        }

    # Standardize type string (GeoPandas gives 'Polygon', 'LineString', etc.)
    g_type = geom_type.lower()

    if "polygon" in g_type:
        return {
            "measurement": geom.area,
            "unit": "m²",
            "measurement_status": "COMPLETED"
        }
    
    elif "linestring" in g_type:
        return {
            "measurement": geom.length,
            "unit": "m",
            "measurement_status": "COMPLETED"
        }
        
    elif "point" in g_type:
        return {
            "measurement": None,
            "unit": None,
            "measurement_status": "NOT_REQUIRED"
        }
        
    else:
        # Fallback for GeometryCollections, MultiPoints, etc.
        return {
            "measurement": None,
            "unit": None,
            "measurement_status": "UNSUPPORTED"
        }
