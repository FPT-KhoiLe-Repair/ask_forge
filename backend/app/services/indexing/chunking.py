# tách PDF -> Pages -> Chunks
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_and_filter(
    filename: str,
    docs: list,
    splitter: RecursiveCharacterTextSplitter,
    min_chars: int,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    # Count total number of pages (each doc represents one page)
    total_pages = len(docs)

    # Split each page into smaller overlapping text segments
    raw_chunks = splitter.split_documents(docs)

    # Filter out short chunks that don't meet the minimum length threshold
    kept = [c for c in raw_chunks if len((c.page_content or "").strip()) >= min_chars]

    contents = []
    page_counters: Dict[int, int] = {}

    for c in kept:
        # Extract 1-based page number from metadata
        page0 = c.metadata.get("page", 0)
        page1 = int(page0) + 1

        # Increment counter for chunks on this page
        page_counters[page1] = page_counters.get(page1, 0) + 1
        chunk_num = page_counters[page1]

        # Build standardized chunk structure
        contents.append({
            "text": c.page_content,
            "page": page1,
            "chunk_id": f"p{page1}_c{chunk_num}",
        })

    # Combine structured content and metadata
    doc_chunks = {"source": filename, "content": contents}
    metrics = {
        "total_pages": total_pages,
        "total_raw_chunks": len(raw_chunks),
        "kept_chunks_after_min_chars": len(contents),
    }

    return doc_chunks, metrics
