"""
PDF text extraction utility using pypdf.
Used for any PDF sources (patents, papers, etc.)
"""
from pypdf import PdfReader
from pathlib import Path
from typing import Optional


def extract_pdf_text(pdf_path: Path, output_path: Optional[Path] = None) -> str:
    """
    Extract all text from a PDF file.
    Optionally saves to output_path.
    """
    reader = PdfReader(str(pdf_path))
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"--- Page {i + 1} ---\n{text}")

    full_text = "\n\n".join(pages_text)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_text, encoding="utf-8")
        print(f"  Saved PDF text: {pdf_path.name} -> {output_path} ({len(full_text)} chars)")

    return full_text


def process_all_pdfs(
    input_dir: Path = Path("data/raw/patents"),
    output_dir: Path = Path("data/raw/patents")
):
    """Process all PDFs in a directory, saving extracted text as .txt files."""
    if not input_dir.exists():
        print(f"  No PDF directory found at {input_dir}, skipping.")
        return

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"  No PDF files found in {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for pdf_file in pdf_files:
        out_file = output_dir / f"{pdf_file.stem}.txt"
        if out_file.exists():
            print(f"  Skipping {pdf_file.name} (already extracted)")
            continue
        try:
            extract_pdf_text(pdf_file, out_file)
        except Exception as e:
            print(f"  Error extracting {pdf_file.name}: {e}")


if __name__ == "__main__":
    process_all_pdfs()
