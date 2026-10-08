from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FeatureResponse(BaseModel):
    feature_id: int | str
    geometry_type: str
    geometry: dict[str, Any] | None
    crs: str | None
    properties: dict[str, Any]
    measurement: float | None = None
    unit: str | None = None
    measurement_status: str | None = None


class FileUploadResponse(BaseModel):
    """Response returned immediately after a successful file upload."""

    id: str
    filename: str
    file_type: str
    size_bytes: int
    status: str
    
    feature_count: int | None = None
    crs: str | None = None
    measurement_crs: str | None = None
    features: list[FeatureResponse] | None = None

    model_config = {"from_attributes": True}


class FileInfoResponse(BaseModel):
    """Response for GET /api/files/{id}/ — file metadata without measurement details."""

    id: str
    filename: str
    file_type: str
    size_bytes: int
    status: str
    error_message: str | None = None
    feature_count: int | None = None
    crs: str | None = None
    measurement_crs: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MeasurementsResponse(BaseModel):
    """Response for GET /api/files/{id}/measurements/ — full feature measurements."""

    file_id: str
    filename: str
    crs: str | None = None
    measurement_crs: str | None = None
    feature_count: int | None = None
    features: list[FeatureResponse] | None = None
