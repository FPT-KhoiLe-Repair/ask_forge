"""
Updated ChromaRepo với query methods cho chat.
"""
from typing import List, Dict, Any, Optional
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from ask_forge.backend.app.core.config import settings

class ChromaRepo:
    """
    Repository class quản lý ChromaDB collections, embeddings, và queries.

    Được khởi tạo 1 lần duy nhất trong AppState (singleton pattern).
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
        self._colletions: dict[str, Any] = {}

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
        return f"{index_name}"

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
    # New methods, MUST CHECK
    def get_collection(self, index_name: str):
        """
        Get existing collection (không tạo mới).

        Raises:
            ValueError: Nếu collection không tồn tại
        """
        try:
            return self.client.get_collection(
                name=self._collection_name(index_name),
                embedding_function=self.embedder,
            )
        except Exception as e:
            raise ValueError(f"Collection '{index_name}' does not exist: {e}")
    def list_collections(self):
        """List tất cả các collection hiện có."""
        return self.client.list_collections()

    def delete_collection(self, index_name: str):
        """Xóa collection."""
        self.client.delete_collection(name=self._collection_name(index_name))
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
    # ------------------------------------------------------------
    # Query & Search (CHO CHAT) (New, must check)
    # ------------------------------------------------------------
    def query(self,
              index_name: str,
              query_text: str,
              n_results: int = 5,
              where: Optional[str] = None,
              where_document: Optional[str] = None
    )-> Dict[str, Any]:
        """
        Query vector database để tìm chunks tương tự.

        Args:
            index_name: Tên index cần query
            query_text: User query (tự động embedding)
            n_results: Số lượng kết quả trả về (top-k)
            where: Filter theo metadata (e.g., {"source": "file.pdf"})
            where_document: Filter theo nội dung document

        Returns:
            Dict chứa:
                - ids: List[List[str]] - IDs của chunks
                - documents: List[List[str]] - Nội dung chunks
                - metadatas: List[List[Dict]] - Metadata
                - distances: List[List[float]] - Cosine distances

        Example:
            >>> repo.query(
            ...     "econ101",
            ...     "What is supply and demand?",
            ...     n_results=3
            ... )
        """
        col = self.get_collection(index_name)

        results = col.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
        )

        return results

    def get_context_for_chat(self,
                             index_name: str,
                             query_text: str,
                             n_results: int = 5,
                             min_relevance: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Helper method để lấy context chunks cho chat/RAG.

        Returns:
            List of dicts, mỗi dict chứa:
                - text: Nội dung chunk
                - source: File source
                - page: Page number
                - chunk_id: Chunk ID
                - score: Relevance score (1 - distance)

        Example:
            >>> contexts = repo.get_context_for_chat("econ101", "What is GDP?")
            >>> for ctx in contexts:
            ...     print(f"Page {ctx['page']}: {ctx['text'][:100]}...")
        """
        results = self.query(
            index_name=index_name,
            query_text=query_text,
            n_results=n_results,
        )

        # Flatten results
        contexts = []
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            score = 1 - distance # Convert distance to similarity score

            # Filter by minimum relevance
            if score < min_relevance:
                continue

            contexts.append({
                'text': results['documents'][0][i],
                'source': results['metadatas'][0][i]['source'],
                'page': results['metadatas'][0][i]['page'],
                'chunk_id': results['metadatas'][0][i]['chunk_id'],
                'score': round(score, 4),
            })
        return contexts

    def get_collection_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Lấy thống kê về collection.

        Returns:
            Dict chứa:
                - count: Số lượng chunks
                - name: Tên collection
                - metadata: Collection metadata
        """
        col = self.get_collection(index_name)
        return {
            'count': col.count(),
            'name': col.name,
            'metadata': col.metadata,
        }