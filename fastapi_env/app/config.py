"""
تنظیمات برنامه
مدیریت متغیرهای محیطی و تنظیمات
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """
    کلاس تنظیمات برنامه
    """
    
    # Application
    app_name: str = "FastAPI Tutorial"
    version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./fastapi_tutorial.db"
    database_url_test: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Email (Optional)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Database URL for different environments
def get_database_url():
    """
    دریافت URL پایگاه داده بر اساس محیط
    """
    if settings.environment == "test":
        return settings.database_url_test or "sqlite:///./test.db"
    return settings.database_url
