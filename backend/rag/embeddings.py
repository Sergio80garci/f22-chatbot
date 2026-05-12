"""Factory de embeddings — selecciona provider según config."""
from functools import lru_cache

from backend.config import settings


@lru_cache(maxsize=1)
def get_embeddings():
    """Retorna el embedder según settings.embedding_provider.

    - 'hf' (default, producción): sentence-transformers in-process, sin servicios externos.
    - 'ollama': requiere Ollama corriendo en ollama_base_url.
    """
    provider = settings.embedding_provider.lower()

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )

    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=settings.hf_embed_model,
        model_kwargs={
            "trust_remote_code": True,
            "device": "cpu",
            "prompts": {
                "passage": "search_document: ",
                "query": "search_query: ",
            },
            "default_prompt_name": "passage",
        },
        encode_kwargs={"normalize_embeddings": True, "prompt_name": "passage"},
        query_encode_kwargs={"normalize_embeddings": True, "prompt_name": "query"},
    )
