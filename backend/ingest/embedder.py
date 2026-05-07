import os
import time

import chromadb
from langchain_core.documents import Document

COLLECTION_NAME = "f22_knowledge_base"


def embed_and_store(documents: list[Document], env: dict) -> int:
    provider    = env.get("LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama"))
    chroma_path = env.get("CHROMA_PATH", "./data/chroma_db")

    client = chromadb.PersistentClient(path=chroma_path)

    if provider == "groq":
        # HuggingFace embeddings — corre en CPU, sin Ollama requerido
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        hf_model = env.get("HF_EMBED_MODEL", os.getenv("HF_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"))
        ef = SentenceTransformerEmbeddingFunction(model_name=hf_model)
    else:
        import requests
        base_url   = env.get("OLLAMA_BASE_URL", "http://localhost:11434")
        embed_model = env.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=5)
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(
                f"Ollama no responde en {base_url}. "
                "Ejecuta 'ollama serve' en otra terminal.\n"
                f"Detalle: {e}"
            )
        from chromadb.utils import embedding_functions
        ef = embedding_functions.OllamaEmbeddingFunction(
            url=f"{base_url}/api/embeddings",
            model_name=embed_model,
        )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    total = len(documents)
    ids, texts, metadatas = [], [], []

    for i, doc in enumerate(documents):
        doc_id = f"{doc.metadata.get('filename', 'doc')}_{doc.metadata.get('chunk_index', i)}"
        ids.append(doc_id)
        texts.append(doc.page_content)
        metadatas.append({k: str(v) for k, v in doc.metadata.items()})
        print(f"  Procesando chunk {i + 1} de {total}...", end="\r")

    batch_size = 100
    for start in range(0, total, batch_size):
        collection.upsert(
            ids=ids[start:start + batch_size],
            documents=texts[start:start + batch_size],
            metadatas=metadatas[start:start + batch_size],
        )

    print()
    return total
