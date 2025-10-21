from typing import List, Dict, Any
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from ask_forge.backend.app.core.config import settings

class ChromaRepo:
    """
    A repository class that manages ChromaDB collections, embeddings, and document upserts.

    This class provides a clean abstraction layer over Chroma’s `PersistentClient` API,
    allowing AskForge’s backend to create, store, and retrieve vector embeddings for text chunks.
    It automatically handles embedding generation using a specified SentenceTransformer model
    and organizes collections by consistent naming conventions.

    Attributes:
        client (PersistentClient):
            Persistent Chroma client pointing to a directory defined in settings.
        embedder (SentenceTransformerEmbeddingFunction):
            Embedding function used to convert text chunks into vector embeddings.

    Example:
        >>> repo = ChromaRepo()
        >>> chunks = [
        ...     {"src": "chapter1.pdf", "content": [
        ...         {"text": "Economic systems evolved...", "page": 1, "chunk_id": "p1_c1"},
        ...         {"text": "Adam Smith introduced...", "page": 2, "chunk_id": "p2_c1"},
        ...     ]}
        ... ]
        >>> repo.upsert("econ101", chunks)
        >>> print("Data successfully indexed into ChromaDB.")
    """

    def __init__(self):
        """
        Initialize the Chroma repository client and embedding model.

        Loads configuration values from `settings`:
        - `CHROMA_REPOS_PATH`: local directory for persistent Chroma storage.
        - `EMBEDDING_MODEL`: model name for the embedding function.
        - `CHROMA_COLLECTION_PREFIX`: prefix for all collection names.

        Example:
            >>> repo = ChromaRepo()
            >>> print(repo.client)
        """
        self.client = PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL,
        )

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------
    def _collection_name(self, index_name: str) -> str:
        """
        Construct a standardized collection name by applying the configured prefix.

        Args:
            index_name (str): Logical name of the dataset or topic.

        Returns:
            str: A prefixed collection name for ChromaDB storage.

        Example:
            >>> repo._collection_name("econ101")
            "askforge_econ101"
        """
        return f"{settings.CHROMA_COLLECTION_PREFIX}{index_name}"

    # ------------------------------------------------------------
    # Collection Management
    # ------------------------------------------------------------
    def get_or_create(self, index_name: str):
        """
        Retrieve or create a ChromaDB collection for the given index.

        Args:
            index_name (str):
                Logical name of the collection (e.g., "econ101", "management_theory").

        Returns:
            Collection:
                A ChromaDB collection instance ready for upserts or queries.

        Notes:
            - Uses cosine similarity as the vector space metric (`hnsw:space`).
            - Reuses the same embedding function to ensure consistency.
        """
        return self.client.get_or_create_collection(
            name=self._collection_name(index_name),
            embedding_function=self.embedder,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------
    # Data Upsertion
    # ------------------------------------------------------------
    def upsert(self, index_name: str, all_chunks: List[Dict[str, Any]]):
        """
        Insert or update document chunks into the ChromaDB collection.

        Args:
            index_name (str):
                Name of the target collection.
            all_chunks (List[Dict[str, Any]]):
                List of structured chunks, each representing one document source.
                Expected structure:
                ```python
                [
                    {
                        "src": "lecture1.pdf",
                        "content": [
                            {"text": "...", "page": 1, "chunk_id": "p1_c1"},
                            {"text": "...", "page": 1, "chunk_id": "p1_c2"}
                        ]
                    },
                    ...
                ]
                ```

        Behavior:
            - Flattens all chunks from all documents into parallel lists of:
                - `ids` (unique per chunk, format: "src::chunk_id")
                - `documents` (raw text content)
                - `metadatas` (page, chunk_id, and source info)
            - Performs a Chroma `.upsert()` to insert/update embeddings.

        Example:
            >>> repo = ChromaRepo()
            >>> repo.upsert("econ101", all_chunks)
            >>> print("Upsert complete.")

        Notes:
            - Uses SentenceTransformer embeddings for each chunk.
            - Metadata can later be expanded (e.g., add topics, tags, difficulty).
        """
        col = self.get_or_create(index_name)

        ids, docs, metadatas = [], [], []
        for chunk in all_chunks:
            src = chunk["source"]
            for ch in chunk["content"]:
                ids.append(f"{src}::{ch['chunk_id']}")
                docs.append(ch["text"])
                metadatas.append({
                    "source": src,
                    "page": ch["page"],
                    "chunk_id": ch["chunk_id"],
                })
                # Future extension: Add metadata such as topics, tags, difficulty, etc.

        col.upsert(ids=ids, documents=docs, metadatas=metadatas)
