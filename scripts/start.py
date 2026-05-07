"""
Script de inicio para Railway: ingesta documentos si ChromaDB está vacío,
luego arranca el servidor FastAPI.
"""
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
COLLECTION  = os.getenv("CHROMA_COLLECTION", "f22_knowledge_base")
PORT        = os.getenv("PORT", "8001")


def chroma_count() -> int:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return client.get_collection(COLLECTION).count()
    except Exception:
        return 0


if __name__ == "__main__":
    if chroma_count() == 0:
        print("[start] ChromaDB vacío — ejecutando ingestión de documentos F22...")
        result = subprocess.run([sys.executable, "scripts/ingest_documents.py"])
        if result.returncode != 0:
            print("[start] ERROR en ingestión — abortando")
            sys.exit(1)
        print(f"[start] Ingestión completada — {chroma_count()} chunks indexados")
    else:
        print(f"[start] ChromaDB ya tiene {chroma_count()} chunks — saltando ingestión")

    print(f"[start] Iniciando FastAPI en puerto {PORT}...")
    os.execvp("uvicorn", [
        "uvicorn", "backend.api.main:app",
        "--host", "0.0.0.0",
        "--port", PORT,
    ])
