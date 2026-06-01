"""
ChromaDB interface for persistent local vector storage.
Collection: tesla_docs
"""
import chromadb
from pathlib import Path
from typing import List, Dict, Any
from .embedder import LocalEmbedder

CHROMA_DIR = ".chroma"


class VectorStore:
    def __init__(self, collection_name: str = "tesla_docs"):
        self.embedder = LocalEmbedder()
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(
            f"VectorStore ready. Collection '{collection_name}' "
            f"has {self.collection.count()} docs."
        )

    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """Index documents into ChromaDB in batches."""
        total = len(documents)
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            texts = [d["text"] for d in batch]
            metadatas = [d["metadata"] for d in batch]
            ids = [f"doc_{i + j}" for j, _ in enumerate(batch)]
            embeddings = self.embedder.embed(texts)
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(
                f"  Indexed batch {i // batch_size + 1}: "
                f"docs {i} to {i + len(batch)}"
            )
        print(f"Indexing complete. Total: {self.collection.count()} docs.")

    def search(
        self, query: str, n_results: int = 5, where: Dict = None
    ) -> List[Dict]:
        """Retrieve top-k relevant chunks for a query."""
        query_embedding = self.embedder.embed_single(query)
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)
        output = []
        for j in range(len(results["documents"][0])):
            output.append({
                "text": results["documents"][0][j],
                "metadata": results["metadatas"][0][j],
                "score": 1 - results["distances"][0][j],  # cosine similarity
            })
        return output
