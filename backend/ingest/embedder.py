import chromadb
from langchain_core.documents import Document

from backend.config import settings
from backend.rag.embeddings import get_embeddings

COLLECTION_NAME = settings.chroma_collection
_BATCH_SIZE = 50


class _LCEmbeddingFunction:
    """Wrapper ChromaDB-compatible sobre LangChain Embeddings."""

    def __init__(self, embedder):
        self._embedder = embedder

    def name(self) -> str:
        return f"lc-{settings.embedding_provider}-embedding"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._embedder.embed_documents(input)


def embed_and_store(documents: list[Document], env: dict) -> int:
    chroma_path = env.get("CHROMA_PATH", settings.chroma_path)

    provider = settings.embedding_provider
    print(f"  Provider de embeddings: {provider}")
    if provider == "hf":
        print(f"  Modelo HF: {settings.hf_embed_model}")
    else:
        print(f"  Modelo Ollama: {settings.ollama_embed_model} ({settings.ollama_base_url})")
    print(f"  Batch size: {_BATCH_SIZE}")

    ef = _LCEmbeddingFunction(get_embeddings())

    client = chromadb.PersistentClient(path=chroma_path)

    # Borrar colección existente para re-indexar con el nuevo modelo
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Colección anterior eliminada (re-indexación).")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    total = len(documents)
    ids, texts, metadatas = [], [], []

    for i, doc in enumerate(documents):
        doc_id = f"{doc.metadata.get('filename', 'doc')}_{doc.metadata.get('chunk_index', i)}"
        ids.append(doc_id)
        texts.append(doc.page_content)
        metadatas.append({k: str(v) for k, v in doc.metadata.items()})

    num_batches = (total + _BATCH_SIZE - 1) // _BATCH_SIZE
    for batch_num, start in enumerate(range(0, total, _BATCH_SIZE), 1):
        end = min(start + _BATCH_SIZE, total)
        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Batch {batch_num}/{num_batches} — {end} de {total} chunks indexados...", end="\r")

    print()
    return total
