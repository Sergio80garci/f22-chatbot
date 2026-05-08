from collections import defaultdict
import random

import chromadb
from fastapi import APIRouter, BackgroundTasks, HTTPException
from langchain_core.prompts import ChatPromptTemplate
from backend.api.models import DocumentInfo
from backend.config import settings
from backend.rag.pipeline import _build_llm

router = APIRouter()

# Cache for document summaries
summaries_cache: dict[str, str] = {}


def _generate_summary(filename: str, chunks: list[str]) -> None:
    if not chunks or filename in summaries_cache:
        return

    content = "\n\n".join(chunks[:2])
    try:
        llm = _build_llm()
        prompt = f"Resume en 2 líneas máximo el siguiente contenido del documento F22:\n\n{content}"
        chain = ChatPromptTemplate.from_template(prompt) | llm
        response = chain.invoke({})
        summaries_cache[filename] = response.content.strip()
    except Exception:
        summaries_cache[filename] = ""


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(background_tasks: BackgroundTasks):
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        data = col.get(include=["metadatas", "documents"])
    except Exception as e:
        # Don't expose ChromaDB internals to client
        import logging
        logging.error(f"ChromaDB connection error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="No se pudo conectar con la base de datos. Intenta nuevamente.")

    counts: dict[str, dict] = defaultdict(lambda: {"file_type": "", "chunk_count": 0, "chunks": []})
    for meta, doc in zip(data["metadatas"], data["documents"]):
        fname = meta.get("filename", meta.get("source", "unknown"))
        ftype = meta.get("file_type", "unknown")
        counts[fname]["file_type"] = ftype
        counts[fname]["chunk_count"] += 1
        counts[fname]["chunks"].append(doc)

    result = []
    for fname, info in sorted(counts.items()):
        summary = summaries_cache.get(fname, "")
        if not summary:
            background_tasks.add_task(_generate_summary, fname, info["chunks"][:2])
        result.append(DocumentInfo(
            filename=fname,
            file_type=info["file_type"],
            chunk_count=info["chunk_count"],
            summary=summary
        ))

    return result


@router.get("/suggested-questions", response_model=list[str])
async def get_suggested_questions():
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        data = col.get(include=["documents"])
    except Exception as e:
        # Log error but return empty list for graceful degradation
        import logging
        logging.error(f"ChromaDB error in suggested-questions: {e}", exc_info=True)
        return []

    if not data["documents"]:
        return []

    # Select 4 random chunks
    chunks = data["documents"]
    selected_chunks = random.sample(chunks, min(4, len(chunks)))

    # Combine chunks for prompt
    context = "\n\n---\n\n".join(selected_chunks)

    # Generate questions using LLM (Groq o Ollama según LLM_PROVIDER)
    llm = _build_llm()

    prompt = f"""Basándote en el siguiente contenido de documentos F22, genera 4 preguntas aleatorias y concretas que puedan ser respondidas con la información proporcionada. Las preguntas deben ser específicas sobre el contenido dado, no genéricas.

Contenido:
{context}

Preguntas:"""

    chain = ChatPromptTemplate.from_template(prompt) | llm
    response = chain.invoke({})

    # Parse questions
    questions = [q.strip() for q in response.content.split('\n') if q.strip() and q.strip().endswith('?')][:4]

    return questions
