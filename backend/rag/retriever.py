from langchain_core.documents import Document

from backend.config import settings
from backend.rag.vectorstore import get_vectorstore


def retrieve(query: str) -> list[Document]:
    vs = get_vectorstore()
    return vs.similarity_search(query, k=settings.top_k_results)
