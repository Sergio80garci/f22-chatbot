import os
import time

import chromadb
import requests
from chromadb.utils import embedding_functions
from langchain_core.documents import Document

COLLECTION_NAME = "f22_knowledge_base"


def _check_ollama(base_url: str) -> None:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            f"Ollama no responde en {base_url}. "
            "Ejecuta 'ollama serve' en otra terminal.\n"
            f"Detalle: {e}"
        )


def embed_and_store(documents: list[Document], env: dict) -> int:
    base_url = env.get("OLLAMA_BASE_URL", "http://localhost:11434")
    embed_model = env.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    chroma_path = env.get("CHROMA_PATH", "./data/chroma_db")

    _check_ollama(base_url)

    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url=f"{base_url}/api/embeddings",
        model_name=embed_model,
    )

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ollama_ef,
    )

    total = len(documents)
    ids, texts, metadatas = [], [], []

    for i, doc in enumerate(documents):
        doc_id = f"{doc.metadata.get('filename', 'doc')}_{doc.metadata.get('chunk_index', i)}"
        ids.append(doc_id)
        texts.append(doc.page_content)
        metadatas.append({k: str(v) for k, v in doc.metadata.items()})
        print(f"  Procesando chunk {i + 1} de {total}...", end="\r")

    # Upsert in batches of 100 to avoid memory issues
    batch_size = 100
    for start in range(0, total, batch_size):
        batch_ids = ids[start : start + batch_size]
        batch_texts = texts[start : start + batch_size]
        batch_meta = metadatas[start : start + batch_size]
        collection.upsert(ids=batch_ids, documents=batch_texts, metadatas=batch_meta)

    print()
    return total
