"""
High-level retrieval logic.
Performs similarity search and returns formatted context string for the LLM.
"""
from .vectorstore import VectorStore
from typing import List, Dict, Tuple


class Retriever:
    def __init__(self):
        self.vectorstore = VectorStore()

    def retrieve(
        self, query: str, n_results: int = 5
    ) -> Tuple[str, List[Dict]]:
        """
        Returns (context_string, raw_results).
        context_string is formatted for insertion into the LLM prompt.
        """
        results = self.vectorstore.search(query, n_results=n_results)
        if not results:
            return "", []

        context_parts = []
        for i, r in enumerate(results, 1):
            source = r["metadata"].get("work", "Unknown")
            year = r["metadata"].get("year", "")
            chapter = r["metadata"].get("chapter", "")
            source_label = f"{source}"
            if chapter:
                source_label += f" ({chapter})"
            if year:
                source_label += f" [{year}]"
            context_parts.append(f"[Source {i}: {source_label}]\n{r['text']}")

        context_string = "\n\n".join(context_parts)
        return context_string, results

    def get_vectorstore(self) -> VectorStore:
        return self.vectorstore
