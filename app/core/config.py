"""
CEMS Configuration Module
Manages all application settings using Pydantic BaseSettings
"""

from typing import Optional, List, Union
from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    PROJECT_NAME: str = "CEMS - Currency Exchange Management System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database Settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        """Construct database URL from components if not provided"""
        if isinstance(v, str) and v:
            return v
        
        values = info.data
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        ))
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    # CORS Settings - دعم كل التنسيقات
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        """Parse CORS origins - supports multiple formats"""
        if v is None:
            return ["http://localhost:3000"]
        
        if isinstance(v, list):
            return v
        
        if isinstance(v, str):
            # Empty string
            if not v or v.strip() == "":
                return ["http://localhost:3000"]
            
            # JSON array format
            if v.strip().startswith("["):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            
            # Comma-separated format
            origins = [i.strip() for i in v.split(",") if i.strip()]
            return origins if origins else ["http://localhost:3000"]
        
        return ["http://localhost:3000"]
    
    # Security Settings
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_DURATION_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    ALLOWED_DOCUMENT_TYPES: Union[List[str], str] = [
        "application/pdf",
        "image/jpeg",
        "image/png"
    ]
    UPLOAD_DIR: str = "uploads"
    
    @field_validator("ALLOWED_DOCUMENT_TYPES", mode="before")
    def parse_document_types(cls, v):
        """Parse document types - supports multiple formats"""
        if v is None:
            return ["application/pdf", "image/jpeg", "image/png"]
        
        if isinstance(v, list):
            return v
        
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["application/pdf", "image/jpeg", "image/png"]
            
            if v.strip().startswith("["):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            
            types = [i.strip() for i in v.split(",") if i.strip()]
            return types if types else ["application/pdf", "image/jpeg", "image/png"]
        
        return ["application/pdf", "image/jpeg", "image/png"]
    
    # Email Settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Transaction Settings
    TRANSACTION_NUMBER_PREFIX: str = "TRX"
    VAULT_TRANSFER_PREFIX: str = "VTR"
    CUSTOMER_NUMBER_PREFIX: str = "CUS"
    BRANCH_CODE_PREFIX: str = "BR"
    
    # Business Rules
    DEFAULT_BASE_CURRENCY: str = "USD"
    COMMISSION_RATE: float = 0.01
    LARGE_TRANSFER_THRESHOLD: float = 10000.0
    
    # Model Config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()