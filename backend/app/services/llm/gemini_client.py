from functools import lru_cache
import os
import google.genai as genai
from ask_forge.backend.app.core.config import settings

@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("Missing Gemini API key")
    return genai.Client(api_key=api_key)

def get_gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL",settings.GEMINI_MODEL)