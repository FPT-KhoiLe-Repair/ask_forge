from pathlib import Path
import json
from typing import List, Dict, Any

from ask_forge.backend.app.constants import PAGES_JSON_DIR

def write_pages_json(index_name: str, all_chunks: List[Dict[str, Any]]) -> Path:
    """
    Write processed document chunks to a JSON file inside the configured pages directory.

    Each indexed document (or collection of chunks) is saved as a separate JSON file
    named after the given `index_name`. The output is formatted for readability and uses
    UTF-8 encoding.
    """
    out_file = PAGES_JSON_DIR / f"{index_name}.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    return out_file


def read_pages_json(index_name: str) -> List[Dict[str, Any]]:
    """
    Read a previously saved JSON file containing document chunks.

    This function is the inverse of `write_pages_json()`: it retrieves
    preprocessed chunks from the local JSON store for reuse, re-indexing,
    or verification.
    """
    p = PAGES_JSON_DIR / f"{index_name}.json"
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
