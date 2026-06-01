"""
Local embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2  --  384 dims, fast, good quality, 80MB download.
Completely free, runs on CPU.
"""
from sentence_transformers import SentenceTransformer
from typing import List

MODEL_NAME = "all-MiniLM-L6-v2"


class LocalEmbedder:
    def __init__(self, model_name: str = MODEL_NAME):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_embedding_dimension()
        print(f"Embedding model loaded. Dimension: {self.dimension}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors."""
        embeddings = self.model.encode(
            texts, show_progress_bar=False, normalize_embeddings=True
        )
        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text string."""
        return self.embed([text])[0]
