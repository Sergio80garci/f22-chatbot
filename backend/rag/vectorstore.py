from functools import lru_cache

import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from backend.config import settings


def _make_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    client = chromadb.PersistentClient(path=settings.chroma_path)
    try:
        col = client.get_collection(settings.chroma_collection)
        count = col.count()
    except Exception:
        count = 0

    if count == 0:
        raise RuntimeError(
            f"La colección '{settings.chroma_collection}' está vacía o no existe. "
            "Ejecuta /ingest primero para indexar los documentos F22."
        )

    return Chroma(
        client=client,
        collection_name=settings.chroma_collection,
        embedding_function=_make_embeddings(),
    )
