import os
import shutil
import zipfile
from pathlib import Path


def safe_extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """
    Safely extract a ZIP file preventing directory traversal attacks.
    Returns the path to the extracted directory.
    """
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            # Prevent path traversal (e.g., extracting to ../../etc/passwd)
            member_path = Path(member)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("Insecure ZIP archive detected: path traversal attempt.")
            
            # Extract safely
            zf.extract(member, extract_to)
            
    return extract_to


def find_shapefile(extracted_dir: Path) -> Path:
    """
    Find the main .shp file within an extracted directory.
    Raises ValueError if no Shapefile or multiple Shapefiles are found.
    """
    shp_files = list(extracted_dir.rglob("*.shp"))
    
    if not shp_files:
        raise ValueError("No .shp file found in the ZIP archive.")
    if len(shp_files) > 1:
        raise ValueError("Multiple .shp files found. Please upload an archive with a single Shapefile.")
        
    shp_path = shp_files[0]
    
    # Ensure required companion files exist
    required_extensions = [".shx", ".dbf"]
    missing = []
    for ext in required_extensions:
        companion_path = shp_path.with_suffix(ext)
        if not companion_path.exists():
            missing.append(ext)
            
    if missing:
        raise ValueError(f"Shapefile is missing required companion files: {', '.join(missing)}")
        
    return shp_path
