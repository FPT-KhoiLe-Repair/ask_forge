"""
Documented Pydantic models for representing document chunks and indexing responses.

This module defines:
- Chunk: a single piece of extracted text with provenance (page and id).
- DocumentChunks: a group of chunks coming from a single source.
- Metrics: simple indexing metrics summary.
- BuildIndexResponse: response model returned after building an index.
- AddToIndexResponse: extended response for adding files to an existing index.

The models use Field(...) descriptions so their JSON Schema (via .schema() or .schema_json())
is informative for API docs or validation tooling.

Example usage:
    python documented_models.py

    # Create objects
    chunk = Chunk(text="Hello world", page=1, chunk_id="doc1-0")
    doc = DocumentChunks(source="s3://bucket/doc1.pdf", content=[chunk])
    metrics = Metrics(total_pages=10, total_raw_chunks=25, kept_chunks_after_min_chars=20)
    resp = BuildIndexResponse(ok=True, index_name="my-index", total_files="3", message="Index built", metrics=metrics)

    # Serialize
    print(resp.json(indent=2))

    # Get JSON Schema
    print(BuildIndexResponse.schema_json(indent=2))
"""
from typing import List
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    A single chunk of text extracted from a document.

    Attributes:
        text: The textual content of the chunk.
        page: 1-based page number where the chunk was extracted.
        chunk_id: A unique identifier for the chunk (e.g. "<doc-id>-<chunk-index>").
    """
    text: str = Field(..., description="Textual content of the chunk.")
    page: int = Field(..., ge=1, description="1-based page number where the chunk originated.")
    chunk_id: str = Field(..., description="Unique identifier for the chunk.")


class DocumentChunks(BaseModel):
    """
    A collection of chunks that all come from the same source document.

    Attributes:
        source: A string that identifies where the chunks came from (filename, URL, S3 path, etc).
        content: A list of Chunk objects extracted from the source.
    """
    source: str = Field(..., description="Source identifier (filename, URL, S3 path, ...).")
    content: List[Chunk] = Field(..., description="List of chunks extracted from the source.")


class Metrics(BaseModel):
    """
    Simple metrics summary describing indexing results.

    Attributes:
        total_pages: Total pages present in the processed files.
        total_raw_chunks: Total chunks produced before filtering.
        kept_chunks_after_min_chars: Number of chunks retained after applying a min-character filter.
    """
    total_pages: int = Field(..., ge=0, description="Total pages processed across files.")
    total_raw_chunks: int = Field(..., ge=0, description="Total chunks produced before filtering.")
    kept_chunks_after_min_chars: int = Field(..., ge=0, description="Chunks kept after applying min-character threshold.")


class BuildIndexResponse(BaseModel):
    """
    Response returned after a build-index operation.

    Attributes:
        ok: Whether the operation succeeded.
        index_name: Name of the created index.
        total_files: Number of files processed. Kept as a string here to match the original shape;
                     consider changing to int if you control the API.
        message: Human-readable message about the operation.
        metrics: Metrics object summarizing counts from the build.
    """
    ok: bool = Field(..., description="True if index build succeeded.")
    index_name: str = Field(..., description="Name of the index that was built.")
    total_files: str = Field(..., description="Number of files processed (string in this model).")
    message: str = Field(..., description="Human-readable status or explanation message.")
    metrics: Metrics = Field(..., description="Metrics summary for the index operation.")


class AddToIndexResponse(BuildIndexResponse):
    """
    Response returned when adding files to an existing index.

    Inherits all fields from BuildIndexResponse and adds:
        added_files: count of files that were newly added to the index.
    """
    added_files: int = Field(..., ge=0, description="Number of files added to the existing index.")
