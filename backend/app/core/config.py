from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "AskForge Backend"
    APP_PREFIX: str = "/api"

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Chunking
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 300
    MIN_CHARS: int= 300

    # STORAGE
    PAGES_JSON_DIR: str = "data/user_db"

    # Chroma
    CHROMA_PERSIST_DIR: str = ".chroma"
    CHROMA_COLLECTION_PREFIX: str = "askforge_"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    class Config:
        env_file = ".env"

settings = Settings()
