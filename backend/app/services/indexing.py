"""
Updated indexing service - nhận ChromaRepo từ dependency injection.
"""
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.services.pdf_loader import load_pdfs
from ask_forge.backend.app.services.chunking import split_and_filter
from ask_forge.backend.app.services.storage import write_pages_json, read_pages_json
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo

async def build_index(
        files,
        index_name: str,
        repo: ChromaRepo
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
       Build index từ files và upsert vào ChromaDB.

       Args:
           files: List of uploaded files
           index_name: Tên index
           repo: ChromaRepo instance (injected)
    """

    docs_per_file = await load_pdfs(files)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    all_chunks: List[Dict[str, Any]] = []
    metrics_sum = {"total_pages": 0,
                   "total_raw_chunks": 0,
                   "kept_chunks_after_min_chars": 0
    }

    for fname, docs in docs_per_file:
        doc_chunks, m = split_and_filter(fname, docs, splitter, settings.MIN_CHARS)
        all_chunks.append(doc_chunks)
        for k in metrics_sum:
            metrics_sum[k] += m[k]

    # Save to JSON
    write_pages_json(index_name, all_chunks)

    # upsert to Chroma (use singleton repo)
    repo.upsert(index_name, all_chunks)

    return all_chunks, metrics_sum

async def add_to_index(
        files,
        index_name: str,
        repo: ChromaRepo
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
        Add files to existing index.

        Args:
            files: List of uploaded files
            index_name: Tên index
            repo: ChromaRepo instance (injected)
    """
    new_chunks, new_metrics_sum = await build_index(files, index_name, repo)

    # merge JSONS to keep a single pages file
    old = read_pages_json(index_name)
    write_pages_json(index_name, old + new_chunks)

    return new_chunks, new_metrics_sum

def load_index(index_name: str) -> List[Dict[str, Any]]:
    return read_pages_json(index_name)
