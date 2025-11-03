"""
Application configuration settings
"""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App settings
    APP_ENV: str = Field(default="dev", description="Application environment")
    APP_SECRET: str = Field(
        default="change-me-dev-secret", description="Application secret key"
    )
    APP_BASE_URL: str = Field(default="http://localhost:8000", description="Base URL")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="info", description="Log level")

    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="Allowed CORS origins (comma-separated)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # Main Database settings (required in runtime environment)
    DB_CLIENT: str = Field(default="mysql", description="Database client type")
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: int = Field(default=3306, description="Database port")
    DB_NAME: str = Field(..., description="Database name")
    DB_USER: str = Field(..., description="Database username")
    DB_PASSWORD: str = Field(..., description="Database password")

    # Location Database settings (separate database for location endpoints)
    LOCATION_DB_CLIENT: str = Field(
        default="mysql", description="Location database client type"
    )
    LOCATION_DB_HOST: str = Field(
        default="", description="Location database host (defaults to main DB_HOST)"
    )
    LOCATION_DB_PORT: int = Field(default=3306, description="Location database port")
    LOCATION_DB_NAME: str = Field(
        default="your-location-database-name", description="Location database name"
    )
    LOCATION_DB_USER: str = Field(
        default="your-location-database-user", description="Location database username"
    )
    LOCATION_DB_PASSWORD: str = Field(
        default="your-location-database-password",
        description="Location database password",
    )

    # Routing settings
    GRAPHHOPPER_MODE: str = Field(
        default="cloud", description="GraphHopper mode: cloud or selfhost"
    )
    GRAPHHOPPER_API_KEY: str = Field(
        default="", description="GraphHopper API key (for cloud mode)"
    )
    GRAPHHOPPER_BASE_URL: str = Field(
        default="http://graphhopper:8989",
        description="GraphHopper base URL (for selfhost mode)",
    )
    USE_CLOUD_MATRIX: bool = Field(
        default=True,
        description="When in selfhost mode, use GraphHopper Cloud Matrix for optimization",
    )
    # Routing thresholds
    ROUTE_DETOUR_RATIO_THRESHOLD: float = Field(
        default=1.5,
        description="Warn when day total duration exceeds baseline by this ratio",
    )
    ROUTE_STOP_OFFENDER_RATIO: float = Field(
        default=0.5,
        description="Warn when a single VIA adds this ratio of baseline minutes",
    )

    # Maps settings
    MAPTILER_API_KEY: str = Field(default="", description="MapTiler API key")

    # AI settings
    OPENAI_API_KEY: str = Field(
        default="", description="OpenAI API key for AI-powered features"
    )

    # Safety: enforce production DB host by default
    ENFORCE_PROD_DB: bool = Field(
        default=True, description="Fail startup if DB_HOST differs from PROD_DB_HOST"
    )
    PROD_DB_HOST: str = Field(
        default="your-production-db-host",
        description="Expected production DB host when enforcement is enabled",
    )

    @property
    def database_url(self) -> str:
        """Get main database URL"""
        from urllib.parse import quote_plus

        if self.DB_CLIENT.lower() == "mysql":
            # URL encode the password to handle special characters
            encoded_password = quote_plus(self.DB_PASSWORD)
            return (
                f"mysql+pymysql://{self.DB_USER}:{encoded_password}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
            )
        elif self.DB_CLIENT.lower() == "sqlite":
            # SQLite for testing
            if self.DB_HOST == ":memory:":
                return "sqlite:///:memory:"
            else:
                return f"sqlite:///{self.DB_NAME}.db"
        else:
            # Fallback for PostgreSQL if needed
            encoded_password = quote_plus(self.DB_PASSWORD)
            return (
                f"postgresql://{self.DB_USER}:{encoded_password}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

    @property
    def location_database_url(self) -> str:
        """Get location database URL"""
        from urllib.parse import quote_plus

        # Use main DB host if location host is not specified
        location_host = self.LOCATION_DB_HOST or self.DB_HOST

        if self.LOCATION_DB_CLIENT.lower() == "mysql":
            # URL encode the password to handle special characters
            encoded_password = quote_plus(self.LOCATION_DB_PASSWORD)
            return (
                f"mysql+pymysql://{self.LOCATION_DB_USER}:{encoded_password}"
                f"@{location_host}:{self.LOCATION_DB_PORT}/{self.LOCATION_DB_NAME}?charset=utf8mb4"
            )
        elif self.LOCATION_DB_CLIENT.lower() == "sqlite":
            # SQLite for testing
            if location_host == ":memory:":
                return "sqlite:///:memory:"
            else:
                return f"sqlite:///{self.LOCATION_DB_NAME}.db"
        else:
            # Fallback for PostgreSQL if needed
            encoded_password = quote_plus(self.LOCATION_DB_PASSWORD)
            return (
                f"postgresql://{self.LOCATION_DB_USER}:{encoded_password}"
                f"@{location_host}:{self.LOCATION_DB_PORT}/{self.LOCATION_DB_NAME}"
            )

    model_config = ConfigDict(
        env_file=[
            "../.env.production",  # Check parent directory first
            ".env.production",     # Check current directory
            "../.env.local",       # Check parent directory
            ".env.local",          # Check current directory
            "../.env",             # Check parent directory
            ".env"                 # Check current directory
        ],
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    import os
    print(f"❌ Failed to load settings: {e}")
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Environment files checked: parent and current directories")

    # Check which files exist
    env_files = [
        "../.env.production", ".env.production",
        "../.env.local", ".env.local",
        "../.env", ".env"
    ]
    for env_file in env_files:
        exists = os.path.exists(env_file)
        print(f"🔍 {env_file}: {'✅ exists' if exists else '❌ not found'}")

    # Show some key environment variables
    key_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    print(f"🔍 Environment variables:")
    for var in key_vars:
        value = os.environ.get(var, "NOT SET")
        # Mask password for security
        if "PASSWORD" in var and value != "NOT SET":
            value = "*" * len(value)
        print(f"   {var}: {value}")

    raise
