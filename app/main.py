import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings

# Configure module-level logger
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A REST API that accepts geospatial files (KML, Shapefile ZIP), "
            "extracts features, handles CRS transformations, and returns "
            "accurate metric measurements for polygons and line strings."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Ensure the upload directory exists on startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.upload_dir)

    @app.get(
        "/health",
        summary="Health check",
        description="Returns the application name and version. Use this to verify the service is running.",
        tags=["Health"],
    )
    def health_check() -> JSONResponse:
        return JSONResponse(
            content={
                "status": "ok",
                "app": settings.app_name,
                "version": settings.app_version,
            }
        )

    return app


app = create_app()
