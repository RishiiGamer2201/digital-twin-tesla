"""One-time ChromaDB indexing. Run after collect_data.py."""
import sys
import json
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vectorstore import VectorStore

print("=" * 60)
print("   NIKOLA TESLA DIGITAL TWIN  --  VECTOR STORE INDEXING")
print("=" * 60)

docs_path = Path("data/processed/documents.json")
if not docs_path.exists():
    print("[X] ERROR: Run scripts/collect_data.py first!")
    print("   No documents found at:", docs_path)
    sys.exit(1)

docs = json.loads(docs_path.read_text())
print(f"\n Loaded {len(docs)} document chunks")
print(" Indexing into ChromaDB (this takes 5-15 minutes the first time)...")
print("-" * 40)

vs = VectorStore()
vs.add_documents(docs, batch_size=100)

print("\n" + "=" * 60)
print("  [OK] Indexing complete!")
print("  Next: streamlit run app/streamlit_app.py")
print("=" * 60)
