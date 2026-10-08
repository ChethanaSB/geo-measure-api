import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.file import FileUploadResponse
from app.utils.file_utils import save_upload, validate_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a geospatial file",
    description=(
        "Upload a KML file or a ZIP archive containing a Shapefile. "
        "The file is validated, stored, and queued for processing. "
        "Returns an upload receipt with a file ID for subsequent requests."
    ),
    responses={
        400: {"description": "Invalid file type or empty file"},
        413: {"description": "File exceeds the maximum allowed size"},
    },
)
async def upload_file(file: UploadFile) -> FileUploadResponse:
    """
    Accept a geospatial file upload, validate it, and save it to disk.

    Processing (feature extraction and measurements) happens in the same
    request for simplicity. Background task queuing is a future improvement
    documented in the README.
    """
    logger.info("Upload received: filename=%s, content_type=%s", file.filename, file.content_type)

    # Validate extension before touching the filesystem
    try:
        validate_file(file)
    except ValueError as exc:
        logger.warning("Upload rejected: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Stream to disk with size enforcement
    try:
        saved_path, size_bytes = await save_upload(file, settings.max_upload_size_bytes)
    except ValueError as exc:
        msg = str(exc)
        logger.warning("Upload save failed: %s", msg)
        # Distinguish size errors from other validation errors
        if "exceeds the maximum" in msg:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    file_id = saved_path.stem  # UUID hex — the stem of the saved filename
    file_type = Path(file.filename).suffix.lower().lstrip(".")

    logger.info(
        "Upload saved: id=%s, original=%s, size=%d bytes",
        file_id,
        file.filename,
        size_bytes,
    )

    return FileUploadResponse(
        id=file_id,
        filename=file.filename,
        file_type=file_type,
        size_bytes=size_bytes,
        status="UPLOADED",
    )
