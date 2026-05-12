import os
import chromadb
from langchain_core.documents import Document

COLLECTION_NAME = "f22_knowledge_base"
_BATCH_SIZE = 50


class _OllamaEmbeddingFunction:
    """Wrapper ChromaDB-compatible sobre OllamaEmbeddings."""

    def __init__(self, model: str, base_url: str):
        from langchain_ollama import OllamaEmbeddings
        self._model = OllamaEmbeddings(model=model, base_url=base_url)

    def name(self) -> str:
        return "ollama-embedding"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._model.embed_documents(input)


def embed_and_store(documents: list[Document], env: dict) -> int:
    chroma_path = env.get("CHROMA_PATH", "./data/chroma_db")
    ollama_url = env.get("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    embed_model = env.get("OLLAMA_EMBED_MODEL", os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))

    print(f"  Usando Ollama Embeddings: {embed_model} ({ollama_url})")
    print(f"  Batch size: {_BATCH_SIZE}")

    ef = _OllamaEmbeddingFunction(model=embed_model, base_url=ollama_url)

    client = chromadb.PersistentClient(path=chroma_path)

    # Borrar colección existente para re-indexar con el nuevo modelo
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Colección anterior eliminada (cambio de modelo de embeddings).")
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
