import json
from pathlib import Path

from app.schemas import QueryTrace


class TraceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, trace: QueryTrace) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def recent(self, limit: int = 20) -> list[QueryTrace]:
        lines = self.path.read_text(encoding="utf-8").splitlines()
        items = [QueryTrace.model_validate_json(line) for line in lines if line.strip()]
        return list(reversed(items[-limit:]))
