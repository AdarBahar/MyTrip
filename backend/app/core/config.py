"""
Application configuration settings
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App settings
    APP_ENV: str = Field(default="dev", description="Application environment")
    APP_SECRET: str = Field(default="change-me-dev-secret", description="Application secret key")
    APP_BASE_URL: str = Field(default="http://localhost:8000", description="Base URL")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="info", description="Log level")

    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origins (comma-separated)"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # Database settings
    DB_CLIENT: str = Field(default="mysql", description="Database client type")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=3306, description="Database port")
    DB_NAME: str = Field(default="roadtrip_planner", description="Database name")
    DB_USER: str = Field(default="root", description="Database username")
    DB_PASSWORD: str = Field(default="", description="Database password")

    # Routing settings
    GRAPHHOPPER_MODE: str = Field(
        default="cloud",
        description="GraphHopper mode: cloud or selfhost"
    )
    GRAPHHOPPER_API_KEY: str = Field(
        default="",
        description="GraphHopper API key (for cloud mode)"
    )
    GRAPHHOPPER_BASE_URL: str = Field(
        default="http://graphhopper:8989",
        description="GraphHopper base URL (for selfhost mode)"
    )

    # Maps settings
    MAPTILER_API_KEY: str = Field(default="", description="MapTiler API key")

    @property
    def database_url(self) -> str:
        """Get database URL"""
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

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()