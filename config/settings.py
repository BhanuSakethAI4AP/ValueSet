import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database Configuration
    mongo_url: str = "mongodb+srv://pbhanusaketh1602:Bhanu%402002@saketh.qsgehh3.mongodb.net/"
    db_name: str = "valuesets_platform"
    
    # JWT Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Configuration
    app_name: str = "ValueSets Platform API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Cache Configuration
    cache_ttl_minutes: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()