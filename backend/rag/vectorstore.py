from functools import lru_cache

import chromadb
from langchain_chroma import Chroma

from backend.config import settings


def _make_embeddings():
    if settings.llm_provider == "groq":
        # ChromaDB default embedding — mismo modelo usado en ingestión
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        from langchain_chroma import Chroma as _Chroma

        class _DefaultEF:
            """Adaptador para que LangChain use el DefaultEmbeddingFunction de ChromaDB."""
            def __init__(self):
                self._ef = DefaultEmbeddingFunction()
            def embed_documents(self, texts):
                return self._ef(texts)
            def embed_query(self, text):
                return self._ef([text])[0]

        return _DefaultEF()
    else:
        from langchain_ollama import OllamaEmbeddings
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
