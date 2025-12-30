from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Gemini API
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    GEMINI_EMBEDDING_MODEL: str
    
    # Qdrant
    QDRANT_HOST: str
    QDRANT_PORT: Optional[int] = None  # Optional, not needed for Qdrant Cloud
    QDRANT_API_KEY: Optional[str] = None  # Optional, required for Qdrant Cloud
    QDRANT_COLLECTION_NAME: str
    QDRANT_USE_CLOUD: bool = False  # Set to true if using Qdrant Cloud
    QDRANT_VECTOR_SIZE: Optional[int] = None  # Optional, will auto-detect from first embedding if not set
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str
    
    # CORS
    CORS_ORIGINS: str
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

