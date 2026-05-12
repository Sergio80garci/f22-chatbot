from collections import defaultdict
import json
import os
import random

import chromadb
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.api.models import DocumentInfo
from backend.config import settings
from backend.rag.pipeline import _build_llm

router = APIRouter()

_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(settings.chroma_path)), "summaries_cache.json")


def _load_cache() -> dict[str, str]:
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(key: str, value: str) -> None:
    """Guarda solo una entrada sin sobreescribir el resto."""
    if not value:
        return
    existing = _load_cache()
    existing[key] = value
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def _generate_summary(filename: str, chunks: list[str]) -> None:
    if not chunks:
        return
    # No regenerar si ya existe en disco
    if _load_cache().get(filename):
        return

    content = "\n\n".join(chunks[:2])
    try:
        from langchain_core.messages import HumanMessage
        llm = _build_llm()
        response = llm.invoke([HumanMessage(content=f"Resume en 2 líneas máximo el siguiente contenido del documento F22:\n\n{content}")])
        _save_cache(filename, response.content.strip())
    except Exception:
        pass  # No cachear fallos — se reintentará en la próxima petición


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(background_tasks: BackgroundTasks):
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(settings.chroma_collection)
        data = col.get(include=["metadatas", "documents"])
    except Exception as e:
        import logging
        logging.error(f"ChromaDB connection error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="No se pudo conectar con la base de datos. Intenta nuevamente.")

    # Leer cache desde disco en cada petición (archivo pequeño, lectura rápida)
    summaries = _load_cache()

    counts: dict[str, dict] = defaultdict(lambda: {"file_type": "", "chunk_count": 0, "chunks": []})
    for meta, doc in zip(data["metadatas"], data["documents"]):
        fname = meta.get("filename", meta.get("source", "unknown"))
        ftype = meta.get("file_type", "unknown")
        counts[fname]["file_type"] = ftype
        counts[fname]["chunk_count"] += 1
        counts[fname]["chunks"].append(doc)

    result = []
    for fname, info in sorted(counts.items()):
        summary = summaries.get(fname, "")
        if not summary:
            background_tasks.add_task(_generate_summary, fname, info["chunks"][:2])
        result.append(DocumentInfo(
            filename=fname,
            file_type=info["file_type"],
            chunk_count=info["chunk_count"],
            summary=summary
        ))

    return result


_QUESTIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(settings.chroma_path)), "questions_pool.json")


@router.get("/suggested-questions", response_model=list[str])
async def get_suggested_questions():
    try:
        with open(_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Acepta tanto lista plana como dict {filename: [preguntas]}
        if isinstance(data, dict):
            pool = [q for qs in data.values() for q in qs if q]
        else:
            pool = [q for q in data if q]
        if pool:
            return random.sample(pool, min(3, len(pool)))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []
