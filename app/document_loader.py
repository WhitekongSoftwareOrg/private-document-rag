from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class DocumentLoader:
    def load(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        if suffix == ".pdf":
            return self._load_pdf(path)
        if suffix == ".docx":
            return self._load_docx(path)
        return path.read_text(encoding="utf-8")

    def _load_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    def _load_docx(self, path: Path) -> str:
        document = DocxDocument(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(paragraphs).strip()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(normalized)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = normalized[start:end]
        if end < text_length:
            last_space = chunk.rfind(" ")
            if last_space > chunk_size // 2:
                end = start + last_space
                chunk = normalized[start:end]

        chunks.append(chunk.strip())
        if end >= text_length:
            break
        start = max(end - chunk_overlap, start + 1)

    return [chunk for chunk in chunks if chunk]
