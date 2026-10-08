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
    
    # We return the extracted data directly in the upload response for now
    # as per the assignment's synchronous processing allowance.
    feature_count: int | None = None
    crs: str | None = None
    features: list[FeatureResponse] | None = None

    model_config = {"from_attributes": True}
