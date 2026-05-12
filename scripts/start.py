"""
Script de inicio para Cloud Run.
El ChromaDB está pre-generado en data/chroma_db/ y se incluye en la imagen Docker.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
COLLECTION   = os.getenv("CHROMA_COLLECTION", "f22_knowledge_base")
PORT         = os.getenv("PORT", "8080")


def chroma_count() -> int:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return client.get_collection(COLLECTION).count()
    except Exception:
        return 0


if __name__ == "__main__":
    count = chroma_count()
    if count > 0:
        print(f"[start] ChromaDB listo — {count} chunks indexados")
    else:
        print("[start] ADVERTENCIA: ChromaDB vacío. Verifica que data/chroma_db/ esté en la imagen.")

    print(f"[start] Iniciando FastAPI en puerto {PORT}...")
    os.execvp("uvicorn", [
        "uvicorn", "backend.api.main:app",
        "--host", "0.0.0.0",
        "--port", PORT,
    ])
