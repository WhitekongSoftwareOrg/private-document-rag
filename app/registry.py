import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import DocumentSummary


class DocumentRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list_documents(self) -> list[DocumentSummary]:
        raw_items = json.loads(self.path.read_text(encoding="utf-8"))
        return [DocumentSummary.model_validate(item) for item in raw_items]

    def upsert_document(
        self,
        *,
        document_id: str,
        file_name: str,
        source_path: str,
        chunks_indexed: int,
    ) -> DocumentSummary:
        documents = self.list_documents()
        updated = DocumentSummary(
            document_id=document_id,
            file_name=file_name,
            source_path=source_path,
            chunks_indexed=chunks_indexed,
            indexed_at=datetime.now(UTC),
        )

        deduped = [item for item in documents if item.document_id != document_id]
        deduped.append(updated)
        payload = [item.model_dump(mode="json") for item in deduped]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return updated
