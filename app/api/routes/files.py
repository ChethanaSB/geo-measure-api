import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.database.models import FileRecord
from app.schemas.file import FileInfoResponse, FileUploadResponse, MeasurementsResponse
from app.services.file_processor import process_kml
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
        400: {"description": "Invalid file type, empty file, or parsing error"},
        413: {"description": "File exceeds the maximum allowed size"},
    },
)
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """
    Accept a geospatial file upload, validate it, save it to disk, and persist to database.
    """
    logger.info("Upload received: filename=%s, content_type=%s", file.filename, file.content_type)

    try:
        validate_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        saved_path, size_bytes = await save_upload(file, settings.max_upload_size_bytes)
    except ValueError as exc:
        msg = str(exc)
        if "exceeds the maximum" in msg:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    file_id = saved_path.stem
    file_type = Path(file.filename).suffix.lower().lstrip(".")

    # Create initial database record
    db_record = FileRecord(
        id=file_id,
        filename=file.filename,
        file_type=file_type,
        size_bytes=size_bytes,
        status="PROCESSING"
    )
    db.add(db_record)
    db.commit()

    # --- Synchronous Processing ---
    import tempfile
    from app.utils.zip_utils import safe_extract_zip, find_shapefile
    from app.services.file_processor import process_shapefile

    processed_data = {}
    try:
        if file_type == "kml":
            processed_data = process_kml(saved_path)
        elif file_type == "zip":
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                safe_extract_zip(saved_path, tmp_path)
                shp_path = find_shapefile(tmp_path)
                processed_data = process_shapefile(shp_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        # Update DB on success
        db_record.status = "COMPLETED"
        db_record.feature_count = processed_data.get("feature_count")
        db_record.source_crs = processed_data.get("crs")
        db_record.measurement_crs = processed_data.get("measurement_crs")
        db_record.measurements = processed_data.get("features")
        db.commit()

    except Exception as exc:
        # Update DB on failure
        db_record.status = "FAILED"
        db_record.error_message = str(exc)
        db.commit()
        
        logger.error("Processing failed for %s: %s", file_id, exc)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR if not isinstance(exc, ValueError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc))

    return FileUploadResponse(
        id=file_id,
        filename=file.filename,
        file_type=file_type,
        size_bytes=size_bytes,
        status=db_record.status,
        feature_count=db_record.feature_count,
        crs=db_record.source_crs,
        measurement_crs=db_record.measurement_crs,
        features=db_record.measurements,
    )


@router.get(
    "/{file_id}/",
    response_model=FileInfoResponse,
    summary="Get file metadata",
    description="Retrieve metadata for a previously uploaded geospatial file by its ID.",
    responses={404: {"description": "File not found"}},
)
def get_file_info(
    file_id: str,
    db: Session = Depends(get_db)
) -> FileInfoResponse:
    """Return metadata for a specific uploaded file."""
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found."
        )
    return FileInfoResponse(
        id=record.id,
        filename=record.filename,
        file_type=record.file_type,
        size_bytes=record.size_bytes,
        status=record.status,
        error_message=record.error_message,
        feature_count=record.feature_count,
        crs=record.source_crs,
        measurement_crs=record.measurement_crs,
        created_at=record.created_at,
    )


@router.get(
    "/{file_id}/measurements/",
    response_model=MeasurementsResponse,
    summary="Get feature measurements",
    description=(
        "Retrieve the extracted features and their calculated measurements "
        "(area in m² for polygons, length in m for line strings) for a processed file."
    ),
    responses={
        404: {"description": "File not found"},
        400: {"description": "File processing failed or is still in progress"},
    },
)
def get_measurements(
    file_id: str,
    db: Session = Depends(get_db)
) -> MeasurementsResponse:
    """Return the full feature measurements for a specific file."""
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found."
        )
    if record.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Measurements not available. File status is '{record.status}'."
        )
    return MeasurementsResponse(
        file_id=record.id,
        filename=record.filename,
        crs=record.source_crs,
        measurement_crs=record.measurement_crs,
        feature_count=record.feature_count,
        features=record.measurements,
    )
