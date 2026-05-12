from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import HealthResponse
from backend.api.routes.chat import router as chat_router
from backend.api.routes.documents import router as documents_router
from backend.config import settings
from backend.version import VERSION, RELEASE_DATE, STACK

app = FastAPI(
    title="F22 Chatbot API",
    description="API RAG para consultas sobre Formulario 22 SII",
    version=VERSION,
)

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


@app.get("/api/version", tags=["info"])
async def version():
    return {
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "stack": STACK,
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    if settings.llm_provider.lower() == "ollama":
        llm_status = f"ok (ollama/{settings.ollama_llm_model})"
    else:
        llm_status = f"ok (groq/{settings.groq_model})"

    chunks = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        chunks = col.count()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"

    overall = "ok" if chroma_status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        llm=llm_status,
        chromadb=chroma_status,
        chunks_indexed=chunks,
    )


@app.get("/", tags=["root"])
async def root():
    return {"message": f"F22 Chatbot API v{VERSION} — visita /docs para la documentación"}
