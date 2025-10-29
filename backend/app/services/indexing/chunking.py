# tách PDF -> Pages -> Chunks
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_and_filter(
    filename: str,
    docs: list,
    splitter: RecursiveCharacterTextSplitter,
    min_chars: int,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Splits PDF pages into smaller text chunks and filters out short or empty chunks.

    This function is typically used after loading a PDF with LangChain’s `PyPDFLoader`.
    It splits each page into overlapping chunks using a text splitter, then filters out
    chunks below a specified minimum character threshold. Each remaining chunk is labeled
    with a unique chunk ID for traceability.

    Args:
        filename (str):
            The original filename of the PDF (used as the `source` identifier).
        docs (list):
            A list of LangChain `Document` objects representing PDF pages.
        splitter (RecursiveCharacterTextSplitter):
            The LangChain text splitter instance that defines how to chunk text (by size and overlap).
        min_chars (int):
            Minimum number of non-space characters required to keep a chunk.
            Chunks shorter than this will be discarded.

    Returns:
        Tuple[Dict[str, Any], Dict[str, int]]:
            A tuple containing:
            - **doc_chunks (Dict[str, Any])**:
                Structured output with source filename and filtered content list:
                ```python
                {
                    "source": "example.pdf",
                    "content": [
                        {"text": "...", "page": 1, "chunk_id": "p1_c1"},
                        {"text": "...", "page": 1, "chunk_id": "p1_c2"},
                        ...
                    ]
                }
                ```
            - **metrics (Dict[str, int])**:
                Summary statistics about the chunking process:
                ```python
                {
                    "total_pages": 5,
                    "total_raw_chunks": 123,
                    "kept_chunks_after_min_chars": 87
                }
                ```

    Example:
        >>> splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        >>> doc_chunks, metrics = split_and_filter("sample.pdf", docs, splitter, min_chars=50)
        >>> print(metrics)
        {'total_pages': 12, 'total_raw_chunks': 340, 'kept_chunks_after_min_chars': 310}

    Notes:
        - Each chunk is tagged with its originating **page number** and a sequential **chunk_id**.
        - This function is commonly paired with a vector store ingestion step (e.g., ChromaDB upsert).
        - The filtering step helps exclude meaningless fragments (e.g., whitespace or OCR noise).
    """
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
