"""One-time data collection. Run this first."""
import sys
import os
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection.scraper import (
    scrape_tesla_autobiography,
    scrape_tesla_articles,
    scrape_wikiquote,
    scrape_wikipedia_tesla,
)
from src.data_collection.youtube_loader import download_all
from src.data_collection.pdf_loader import process_all_pdfs
from src.data_collection.preprocessor import process_all
import json

print("=" * 60)
print("  NIKOLA TESLA DIGITAL TWIN -- DATA COLLECTION")
print("=" * 60)

print("\nSTEP 1: Downloading Tesla's autobiography (My Inventions)")
print("-" * 40)
scrape_tesla_autobiography()

print("\nSTEP 2: Downloading Tesla's published articles")
print("-" * 40)
scrape_tesla_articles()

print("\nSTEP 3: Downloading Tesla quotes (Wikiquote)")
print("-" * 40)
scrape_wikiquote()

print("\nSTEP 4: Downloading Wikipedia biography")
print("-" * 40)
scrape_wikipedia_tesla()

print("\nSTEP 5: Downloading YouTube documentary transcripts")
print("-" * 40)
download_all()

print("\nSTEP 6: Processing any PDF files")
print("-" * 40)
process_all_pdfs()

print("\n" + "=" * 60)
print("  STEP 7: Processing and chunking documents")
print("=" * 60)
docs = process_all()
out = Path("data/processed/documents.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(docs, indent=2))
print(f"\nSaved {len(docs)} chunks to {out}")
print("=" * 60)
print("  Data collection complete! Next: python scripts/build_vectorstore.py")
print("=" * 60)
