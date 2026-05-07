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

# CORS: lista separada por comas en variable de entorno ALLOWED_ORIGINS
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    if settings.llm_provider == "groq":
        llm_status = "ok (groq)" if settings.groq_api_key else "error: GROQ_API_KEY no configurada"
    else:
        try:
            r = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
            llm_status = "ok" if r.ok else f"error {r.status_code}"
        except Exception as e:
            llm_status = f"unavailable: {e}"

    chunks = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        chunks = col.count()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"

    overall = "ok" if "ok" in llm_status and chroma_status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        ollama=llm_status,
        chromadb=chroma_status,
        chunks_indexed=chunks,
    )


@app.get("/", tags=["root"])
async def root():
    return {"message": "F22 Chatbot API — visita /docs para la documentación"}
