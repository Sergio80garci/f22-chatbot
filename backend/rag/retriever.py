from langchain_core.documents import Document

from backend.config import settings
from backend.rag.vectorstore import get_vectorstore


def retrieve(query: str) -> list[Document]:
    vs = get_vectorstore()
    results_with_scores = vs.similarity_search_with_score(
        query, k=settings.top_k_results
    )
    # Filter low-relevance results (ChromaDB uses L2 distance; lower = better)
    # Threshold ~1.4 corresponds roughly to cosine similarity > 0.3
    filtered = [doc for doc, score in results_with_scores if score < 1.4]
    return filtered if filtered else [doc for doc, _ in results_with_scores[:2]]
