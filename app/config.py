import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    MAX_FILE_SIZE_MB: int = 10

    # Azure Document Intelligence
    AZURE_DI_ENDPOINT: str = os.getenv("AZURE_DI_ENDPOINT", "")
    AZURE_DI_KEY: str = os.getenv("AZURE_DI_KEY", "")
    AZURE_DI_API_VERSION: str = os.getenv(
        "AZURE_DI_API_VERSION", "2024-11-30"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
