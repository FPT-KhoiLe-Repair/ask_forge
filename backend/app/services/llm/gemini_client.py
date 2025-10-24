from functools import lru_cache
import os
from dotenv import load_dotenv
import google.genai as genai

DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    # load_dotenv("./.env")
    # api_key = os.environ.get("GEMINI_API_KEY")
    # Nhớ xóa code này và đổi API và lưu vào env mới
    api_key = "AIzaSyD-2l71SRihM6M65yOZqh_dWRhVZ8OxohI"
    if not api_key:
        raise RuntimeError("Missing Gemini API key")
    return genai.Client(api_key=api_key)

def get_gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL",DEFAULT_GEMINI_MODEL)