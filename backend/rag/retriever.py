from langchain_core.documents import Document

from backend.config import settings
from backend.rag.vectorstore import get_vectorstore


def retrieve(query: str) -> list[Document]:
    """Retorna docs relevantes filtrados por min_relevance_score.

    Si ningún chunk supera el umbral, retorna lista vacía → la pipeline
    interpretará esto como "fuera del dominio F22" y dará respuesta de rechazo.
    """
    vs = get_vectorstore()
    pairs = vs.similarity_search_with_relevance_scores(
        query, k=settings.top_k_results
    )
    threshold = settings.min_relevance_score
    return [doc for doc, score in pairs if score >= threshold]


def retrieve_with_scores(query: str) -> list[tuple[Document, float]]:
    """Versión que retorna también los scores — útil para debugging."""
    vs = get_vectorstore()
    return vs.similarity_search_with_relevance_scores(
        query, k=settings.top_k_results
    )
