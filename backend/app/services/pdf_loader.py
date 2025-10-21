from tempfile import NamedTemporaryFile
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader

async def load_pdfs(files: List[UploadFile]):
    """
    Asynchronously loads and extracts text content from uploaded PDF files.

    This function:
      1. Temporarily saves each uploaded file to disk.
      2. Uses `PyPDFLoader` from LangChain to load and parse the PDF into pages.
      3. Returns a list of tuples containing the filename and the parsed document objects.
      4. Cleans up temporary files after processing.

    Args:
        files (List[UploadFile]):
            A list of FastAPI `UploadFile` objects representing uploaded PDFs.

    Returns:
        List[Tuple[str, List[Document]]]:
            A list where each item is a tuple: (filename, list_of_document_pages)
            - `filename`: the original name of the uploaded file.
            - `list_of_document_pages`: a list of LangChain Document objects, one per PDF page.

    Example:
        >>> # Inside an async FastAPI endpoint
        >>> result = await load_pdfs(files)
        >>> for name, docs in result:
        >>>     print(f"{name} -> {len(docs)} pages loaded")

    Notes:
        - Uses NamedTemporaryFile to create temporary storage for each PDF.
        - Ensures cleanup (temporary file removal) even if errors occur.
        - Suitable for FastAPI async routes handling multiple PDF uploads.
    """
    docs_per_file = []
    for uf in files:
        # Ensure file ends with .pdf suffix (some UploadFiles may not include it)
        suffix = ".pdf" if not uf.filename.lower().endswith(".pdf") else ""
        tmp_path = None
        try:
            # Save uploaded content to a temporary file
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(await uf.read())
                tmp_path = tmp_file.name

            # Load the PDF using LangChain’s community loader
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()

            # Store results (filename, parsed documents)
            docs_per_file.append((uf.filename, docs))

        finally:
            # Clean up temporary file after processing
            if tmp_path:
                try:
                    import os
                    os.remove(tmp_path)
                except Exception:
                    pass

    return docs_per_file