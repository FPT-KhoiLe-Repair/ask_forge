# PDF loaders, mine detectors
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader

async def load_pdfs(files: List[UploadFile]):
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