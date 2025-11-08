"""
Updated ChromaRepo với query methods cho chat.
"""
from typing import List, Dict, Any, Optional
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from ask_forge.backend.app.core.config import settings

class ChromaRepo:
    def __init__(self):
        self.client = PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL,
        )
        self._collections: dict[str, Any] = {}

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------
    def _collection_name(self, index_name: str) -> str:
        return f"{index_name}"

    # ------------------------------------------------------------
    # Collection Management
    # ------------------------------------------------------------
    def get_or_create(self, index_name: str):
        return self.client.get_or_create_collection(
            name=self._collection_name(index_name),
            embedding_function=self.embedder,
            metadata={"hnsw:space": "cosine"},
        )

    # New methods, MUST CHECK
    def get_collection(self, index_name: str):
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
    def upsert(self, index_name: str, all_chunks: List[Dict[str, Any]], batch_size: int = 3000):
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

        n = len(ids)
        for i in range(0, n, batch_size):
            j = min(i + batch_size, n)
            col.upsert(
                ids=ids[i:j],
                documents=docs[i:j],
                metadatas=metadatas[i:j],
            )
    # ------------------------------------------------------------
    # Query & Search (CHO CHAT) (New, must check)
    # ------------------------------------------------------------
    def _query(self,
               index_name: str,
               query_text: str,
               n_results: int = 5,
               where: Optional[str] = None,
               where_document: Optional[str] = None
               )-> Dict[str, Any]:
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
                             min_relevance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        results = self._query(
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
        col = self.get_collection(index_name)
        return {
            'count': col.count(),
            'name': col.name,
            'metadata': col.metadata,
        }