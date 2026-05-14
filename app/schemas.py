from datetime import datetime

from pydantic import BaseModel, Field


class IngestDirectoryRequest(BaseModel):
    directory: str = Field(..., description="Absolute or relative path to a local directory")


class IngestResponse(BaseModel):
    document_id: str
    file_name: str
    chunks_indexed: int
    source_path: str


class DocumentSummary(BaseModel):
    document_id: str
    file_name: str
    source_path: str
    chunks_indexed: int
    indexed_at: datetime


class ChatQueryRequest(BaseModel):
    question: str
    top_k: int | None = None


class ContextChunk(BaseModel):
    document_id: str
    file_name: str
    chunk_index: int
    score: float
    text: str


class QueryTraceContext(BaseModel):
    file_name: str
    chunk_index: int
    score: float
    text_preview: str


class QueryTrace(BaseModel):
    trace_id: str
    question: str
    top_k: int
    embedding_model: str
    ollama_model: str
    query_embedding_dimension: int
    prompt_preview: str
    retrieval_time_ms: int
    generation_time_ms: int
    total_time_ms: int
    retrieved_contexts: list[QueryTraceContext]
    answer_preview: str
    created_at: datetime


class ChatQueryResponse(BaseModel):
    answer: str
    contexts: list[ContextChunk]
    trace: QueryTrace | None = None
