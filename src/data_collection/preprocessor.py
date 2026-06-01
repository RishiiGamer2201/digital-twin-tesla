"""
Cleans raw text and splits into chunks for indexing.
Target chunk size: 512 tokens, 64 token overlap.
Each chunk carries metadata: source, topic, scientist.
"""
import re
import json
from pathlib import Path
from typing import List, Dict

CHUNK_SIZE = 512       # words (approx tokens)
CHUNK_OVERLAP = 64     # word overlap between chunks


def clean_text(text: str) -> str:
    """Remove noise: extra whitespace, HTML artifacts, page numbers."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?m)^\s*\d+\s*$', '', text)  # standalone page numbers
    text = re.sub(r'\[edit\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)  # reference markers like [1], [23]
    return text.strip()


def word_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def process_source(filepath: Path, source_type: str, metadata: dict) -> List[Dict]:
    """Process a single file into a list of document dicts."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_text(text)
    chunks = word_chunks(cleaned)
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "text": chunk,
            "metadata": {
                **metadata,
                "source_type": source_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "filepath": str(filepath),
            }
        }
        documents.append(doc)
    return documents


def process_all(raw_dir: Path = Path("data/raw")) -> List[Dict]:
    """Walk all raw data and produce chunked documents."""
    all_docs = []

    # Tesla Autobiography ("My Inventions")
    auto_dir = raw_dir / "autobiography"
    if auto_dir.exists():
        for ch_file in sorted(auto_dir.glob("*.txt")):
            docs = process_source(
                ch_file,
                source_type="autobiography",
                metadata={
                    "scientist": "Nikola Tesla",
                    "work": "My Inventions (Autobiography)",
                    "chapter": ch_file.stem.replace("_", " ").title(),
                    "year": "1919",
                    "topic": "autobiography"
                }
            )
            all_docs.extend(docs)

    # Tesla Articles
    articles_dir = raw_dir / "articles"
    if articles_dir.exists():
        for afile in articles_dir.glob("*.txt"):
            docs = process_source(
                afile,
                source_type="article",
                metadata={
                    "scientist": "Nikola Tesla",
                    "work": afile.stem.replace("_", " ").title(),
                    "year": "1890-1910",
                    "topic": "electrical engineering"
                }
            )
            all_docs.extend(docs)

    # Interviews, Wikiquote, Wikipedia
    interview_dir = raw_dir / "interviews"
    if interview_dir.exists():
        for ifile in interview_dir.glob("*.txt"):
            docs = process_source(
                ifile,
                source_type="interview",
                metadata={
                    "scientist": "Nikola Tesla",
                    "work": ifile.stem.replace("_", " ").title(),
                    "year": "various",
                    "topic": "general"
                }
            )
            all_docs.extend(docs)

    # YouTube documentary transcripts
    yt_dir = raw_dir / "youtube"
    if yt_dir.exists():
        for tfile in yt_dir.glob("*.txt"):
            docs = process_source(
                tfile,
                source_type="video_transcript",
                metadata={
                    "scientist": "Nikola Tesla",
                    "work": tfile.stem.replace("_", " ").title(),
                    "year": "modern",
                    "topic": "documentary"
                }
            )
            all_docs.extend(docs)

    # Patent texts (if any PDFs were processed)
    patents_dir = raw_dir / "patents"
    if patents_dir.exists():
        for pfile in patents_dir.glob("*.txt"):
            docs = process_source(
                pfile,
                source_type="patent",
                metadata={
                    "scientist": "Nikola Tesla",
                    "work": pfile.stem.replace("_", " ").title(),
                    "year": "1886-1928",
                    "topic": "patents"
                }
            )
            all_docs.extend(docs)

    print(f"Total documents after processing: {len(all_docs)}")
    return all_docs


if __name__ == "__main__":
    docs = process_all()
    out = Path("data/processed/documents.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(docs, indent=2))
    print(f"Saved to {out}")
