import logging
import pathlib
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
ROOT_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent.parent.parent.parent.resolve()

class BackendBaseSettings:
    """
    Base settings for the FastAPI application.
    """
    TITLE: str = "GlitchAgent"
    VERSION: str = "0.1"
    TIMEZONE: str = "UTC"
    DESCRIPTION: str = "GlitchAgent API"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", 8000))
    
    @property
    def DOCS_URL(self) -> str | None:
        return "/docs" if self.ENVIRONMENT == "development" else None
        
    @property
    def REDOC_URL(self) -> str | None:
        return "/redoc" if self.ENVIRONMENT == "development" else None
        
    @property
    def OPENAPI_URL(self) -> str | None:
        return "/openapi.json" if self.ENVIRONMENT == "development" else None

    API_PREFIX: str = "/api"
    OPENAPI_PREFIX: str = ""
    NUMBER_OF_WORKERS: int = 4
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = f"logs/app_{ENVIRONMENT}_{datetime.now().strftime('%Y%m%d')}.log"
    os.makedirs("logs", exist_ok=True)
    
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    BACKUP: int = 7
    
    class Config:
        case_sensitive: bool = True
        env_file: str = f"{str(ROOT_DIR)}/.env"
        validate_assignment: bool = True

    @property
    def set_backend_app_attributes(self) -> dict[str, str | bool | None]:
        """
        Set all `FastAPI` class' attributes with the custom values defined in `BackendBaseSettings`.
        """
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL,
            "openapi_prefix": self.OPENAPI_PREFIX,
            "api_prefix": self.API_PREFIX,
        }