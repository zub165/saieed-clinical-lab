from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Saieed Clinical Laboratory"
    admin_email: str = "admin@saieedlab.com"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./saieed_lab.db")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Production settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "4"))
    reload: bool = os.getenv("RELOAD", "False").lower() == "true"
    
    # SSL Configuration
    ssl_keyfile: str = os.getenv("SSL_KEYFILE", "")
    ssl_certfile: str = os.getenv("SSL_CERTFILE", "")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 