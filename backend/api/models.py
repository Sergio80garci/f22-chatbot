from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Pregunta sobre F22 (máx 2000 caracteres)")
    session_id: Optional[str] = Field(default="default", max_length=100)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str
    related_questions: list[str] = []


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    chunk_count: int
    summary: str = ""


class HealthResponse(BaseModel):
    status: str
    llm: str
    chromadb: str
    chunks_indexed: int
