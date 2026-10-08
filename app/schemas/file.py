from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Response returned immediately after a successful file upload."""

    id: str
    filename: str
    file_type: str
    size_bytes: int
    status: str

    model_config = {"from_attributes": True}
