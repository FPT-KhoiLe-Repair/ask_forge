from pathlib import Path
from .core.config import settings

PAGES_JSON_DIR = Path(settings.PAGES_JSON_DIR)
PAGES_JSON_DIR.mkdir(parents=True, exist_ok=True)