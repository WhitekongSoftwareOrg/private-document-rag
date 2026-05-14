from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from app.config import Settings
from app.document_loader import DocumentLoader, SUPPORTED_EXTENSIONS, chunk_text
from app.embedder import EmbeddingService
from app.ollama import OllamaService
from app.registry import DocumentRegistry
from app.schemas import ChatQueryResponse, ContextChunk, IngestResponse, QueryTrace, QueryTraceContext
from app.store import VectorStore
from app.tracing import TraceStore


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.loader = DocumentLoader()
        self.embedder = EmbeddingService(settings.embedding_model)
        self.store = VectorStore(
            path=str(settings.qdrant_path),
            collection_name=settings.qdrant_collection,
            vector_size=self.embedder.dimension,
        )
        self.registry = DocumentRegistry(settings.app_data_dir / "documents.json")
        self.trace_store = TraceStore(settings.trace_path)
        self.generator = OllamaService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    def list_documents(self):
        return self.registry.list_documents()

    def list_traces(self, limit: int = 20):
        return self.trace_store.recent(limit=limit)

    def ingest_file(self, path: Path) -> IngestResponse:
        text = self.loader.load(path)
        chunks = chunk_text(text, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            raise ValueError(f"No text could be extracted from {path.name}")

        document_id = str(uuid4())
        vectors = self.embedder.embed_texts(chunks)
        items = []

        for chunk_index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            items.append(
                {
                    "vector": vector,
                    "payload": {
                        "document_id": document_id,
                        "file_name": path.name,
                        "source_path": str(path.resolve()),
                        "chunk_index": chunk_index,
                        "text": chunk,
                    },
                }
            )

        self.store.upsert_chunks(items)
        self.registry.upsert_document(
            document_id=document_id,
            file_name=path.name,
            source_path=str(path.resolve()),
            chunks_indexed=len(chunks),
        )
        return IngestResponse(
            document_id=document_id,
            file_name=path.name,
            chunks_indexed=len(chunks),
            source_path=str(path.resolve()),
        )

    def ingest_directory(self, directory: Path) -> list[IngestResponse]:
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        responses: list[IngestResponse] = []
        for path in sorted(directory.iterdir()):
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            responses.append(self.ingest_file(path))
        return responses

    async def answer_question(self, question: str, top_k: int) -> ChatQueryResponse:
        total_start = perf_counter()
        query_vector = self.embedder.embed_query(question)
        retrieval_start = perf_counter()
        search_results = self.store.search(query_vector, top_k=top_k)
        retrieval_time_ms = int((perf_counter() - retrieval_start) * 1000)
        contexts = [
            {
                "document_id": point.payload["document_id"],
                "file_name": point.payload["file_name"],
                "chunk_index": point.payload["chunk_index"],
                "score": float(point.score),
                "text": point.payload["text"],
            }
            for point in search_results
        ]
        if not contexts:
            return ChatQueryResponse(
                answer="No indexed context is available yet. Upload a document before asking questions.",
                contexts=[],
            )
        prompt = self.generator.build_prompt(question, contexts)
        generation_start = perf_counter()
        answer = await self.generator.generate_answer(question, contexts)
        generation_time_ms = int((perf_counter() - generation_start) * 1000)
        total_time_ms = int((perf_counter() - total_start) * 1000)
        trace = QueryTrace(
            trace_id=str(uuid4()),
            question=question,
            top_k=top_k,
            embedding_model=self.settings.embedding_model,
            ollama_model=self.settings.ollama_model,
            query_embedding_dimension=len(query_vector),
            prompt_preview=prompt[:1200],
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            total_time_ms=total_time_ms,
            retrieved_contexts=[
                QueryTraceContext(
                    file_name=item["file_name"],
                    chunk_index=item["chunk_index"],
                    score=item["score"],
                    text_preview=item["text"][:350],
                )
                for item in contexts
            ],
            answer_preview=answer[:1200],
            created_at=datetime.now(UTC),
        )
        self.trace_store.append(trace)
        return ChatQueryResponse(
            answer=answer,
            contexts=[ContextChunk(**item) for item in contexts],
            trace=trace,
        )
