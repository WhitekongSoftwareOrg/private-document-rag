from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import get_settings
from app.rag import RAGService
from app.schemas import ChatQueryRequest, ChatQueryResponse, IngestDirectoryRequest, IngestResponse

settings = get_settings()
rag_service = RAGService(settings)

app = FastAPI(title="Private Document Copilot", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "embedding_model": settings.embedding_model,
        "ollama_model": settings.ollama_model,
    }


@app.get("/documents")
def list_documents():
    return rag_service.list_documents()


@app.get("/traces")
def list_traces(limit: int = 10):
    return rag_service.list_traces(limit=limit)


@app.post("/documents/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    destination = settings.app_upload_dir / file.filename

    try:
        content = await file.read()
        destination.write_bytes(content)
        return rag_service.ingest_file(destination)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@app.post("/documents/ingest-directory", response_model=list[IngestResponse])
def ingest_directory(request: IngestDirectoryRequest):
    try:
        return rag_service.ingest_directory(Path(request.directory))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest):
    try:
        return await rag_service.answer_question(
            question=request.question,
            top_k=request.top_k or settings.top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
