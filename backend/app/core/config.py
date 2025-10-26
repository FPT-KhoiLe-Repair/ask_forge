# core/config.py
from pathlib import Path
from typing import List
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).with_name(".env")  # luôn trỏ tới core/.env

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AskForge Backend"
    APP_PREFIX: str = "/api"

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Chunking
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 300
    MIN_CHARS: int = 300

    # Storage
    PAGES_JSON_DIR: str = "data/user_db"

    # Chroma
    CHROMA_PERSIST_DIR: str = ".chroma"
    CHROMA_COLLECTION_PREFIX: str = "askforge_"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Gemini (đặt required hoặc có default tuỳ bạn)
    GEMINI_API_KEY: str = Field(min_length=1)  # thiếu sẽ raise
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")

    # HF
    HF_QG_CHECKPOINT: str = Field(default="Qwen/Qwen2.5-0.6B")
    HF_LOCAL_ONLY: bool = Field(default=False)
    HF_DEVICE_MAP: str = Field(default="auto")
    HF_DTYPE: str = Field(default="")
    HF_LOW_CPU_MEM: bool = Field(default=True)
    HF_TRUST_REMOTE_CODE: bool = Field(default=False)
    HF_PRELOAD_AT_STARTUP: bool = Field(default=False)

    # >>> Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),          # chính xác: core/.env
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
