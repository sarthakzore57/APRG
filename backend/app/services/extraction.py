from pathlib import Path
import mimetypes

import fitz
from docx import Document


TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".cpp", ".c", ".php",
    ".rb", ".go", ".rs", ".sql", ".html", ".css", ".json", ".md", ".txt",
}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text("text") for page in pdf)
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if suffix in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return f"Image file: {path.name}. Use as a student-provided screenshot or figure."
    return f"Unsupported text extraction for {mimetypes.guess_type(path.name)[0] or suffix}."


def clean_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", " ").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 160) -> list[str]:
    cleaned = clean_text(text)
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks
