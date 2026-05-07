from functools import lru_cache

import chromadb
from langchain_chroma import Chroma

from backend.config import settings

MULTILINGUAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def _make_embeddings():
    if settings.llm_provider == "groq":
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MULTILINGUAL_MODEL)

        class _STEmbeddings:
            def embed_documents(self, texts):
                return model.encode(texts, show_progress_bar=False).tolist()
            def embed_query(self, text):
                return model.encode([text], show_progress_bar=False)[0].tolist()

        return _STEmbeddings()
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
