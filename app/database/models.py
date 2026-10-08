from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.database.database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(String(32), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="UPLOADED")
    error_message = Column(Text, nullable=True)
    
    # Geospatial Metadata
    feature_count = Column(Integer, nullable=True)
    source_crs = Column(String(100), nullable=True)
    measurement_crs = Column(String(100), nullable=True)
    
    # We store the extracted feature info + measurements here as JSON.
    # This avoids over-engineering a highly relational schema for feature-level
    # storage unless requested, matching the assignment's simplicity mandate.
    measurements = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
