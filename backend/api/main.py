import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import HealthResponse
from backend.api.routes.chat import router as chat_router
from backend.api.routes.documents import router as documents_router
from backend.config import settings

app = FastAPI(
    title="F22 Chatbot API",
    description="API RAG para consultas sobre Formulario 22 SII",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Only frontend dev server
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type"],  # Only necessary headers
)

app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    # Check Ollama
    try:
        r = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        ollama_status = "ok" if r.ok else f"error {r.status_code}"
    except Exception as e:
        ollama_status = f"unavailable: {e}"

    # Check ChromaDB
    chunks = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        chunks = col.count()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"

    overall = "ok" if ollama_status == "ok" and chroma_status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        ollama=ollama_status,
        chromadb=chroma_status,
        chunks_indexed=chunks,
    )


@app.get("/", tags=["root"])
async def root():
    return {"message": "F22 Chatbot API — visita /docs para la documentación"}
