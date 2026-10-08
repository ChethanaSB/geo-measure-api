import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".kml", ".zip"}


def validate_file(file: UploadFile) -> None:
    """
    Validate the uploaded file before any processing.

    Raises ValueError with a descriptive message if validation fails.
    Keeping validation separate from the route makes it easy to test
    and reuse without coupling to FastAPI's request/response cycle.
    """
    if not file.filename:
        raise ValueError("No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )


def get_safe_filename(original_filename: str) -> str:
    """
    Generate a unique filename using UUID4 while preserving the original extension.

    Using a random UUID avoids:
    - filename collisions between uploads
    - path traversal attacks (e.g. '../../etc/passwd.kml')
    - information leakage from original filenames
    """
    suffix = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


async def save_upload(file: UploadFile, max_size_bytes: int) -> tuple[Path, int]:
    """
    Stream the uploaded file to disk, enforcing a maximum size limit.

    Returns:
        (saved_path, total_bytes_written)

    Raises:
        ValueError: if the file exceeds max_size_bytes or is empty.

    Why stream in chunks instead of reading all at once?
    Reading the entire file into memory first would allow a large upload
    to exhaust server memory before we can reject it. Streaming lets us
    stop early the moment we exceed the limit.
    """
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = get_safe_filename(file.filename)
    dest = upload_dir / safe_name

    total_bytes = 0
    chunk_size = 1024 * 64  # 64 KB chunks

    try:
        with dest.open("wb") as f:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    # Remove the partial file before raising
                    dest.unlink(missing_ok=True)
                    raise ValueError(
                        f"File exceeds the maximum allowed size of "
                        f"{max_size_bytes // (1024 * 1024)} MB."
                    )
                f.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    if total_bytes == 0:
        dest.unlink(missing_ok=True)
        raise ValueError("Uploaded file is empty.")

    return dest, total_bytes
