from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    app_name: str = "GeoMeasure API"
    app_version: str = "1.0.0"
    debug: bool = False

    # File upload
    max_upload_size_mb: int = 50
    upload_dir: str = "uploads"

    # Database
    database_url: str = "sqlite:///./geomeasure.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


# Single shared instance used throughout the application
settings = Settings()
