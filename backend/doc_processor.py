"""
doc_processor.py
------------------
Extracts text from uploaded documents (PDF, Word, plain text/markdown) and
splits it into smaller chunks suitable for the knowledge base's TF-IDF
search. This is the "upload a document" path, complementing the manual
Q&A entries — mirrors how ElevenLabs' own knowledge base accepts files.
"""

import re
from pathlib import Path

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")

CHUNK_SIZE = 700       # characters per chunk — roughly a paragraph or two
CHUNK_OVERLAP = 100    # overlap so we don't cut a sentence's context in half


def extract_text(file_path: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix == ".docx":
        return _extract_docx(file_path)
    elif suffix in (".txt", ".md"):
        return Path(file_path).read_text(errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: {SUPPORTED_EXTENSIONS}")


def _extract_pdf(file_path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(file_path: str) -> str:
    import docx
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Splits text into overlapping chunks, breaking on paragraph/sentence
    boundaries where possible rather than mid-word.
    """
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    # Prefer splitting on paragraphs first.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 <= chunk_size:
            current = f"{current}\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            # If a single paragraph is itself too long, hard-split it.
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i:i + chunk_size])
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)

    return chunks
