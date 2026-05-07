"""
Script principal de ingestión de documentos F22.
Uso: python scripts/ingest_documents.py
"""
import os
import sys
import time
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from backend.ingest.chunker import chunk_document
from backend.ingest.embedder import embed_and_store
from backend.ingest.extract import SUPPORTED_EXTENSIONS, extract_file

ENV = {
    "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "llama3.2"),
    "OLLAMA_EMBED_MODEL": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    "CHROMA_PATH": os.getenv("CHROMA_PATH", "./data/chroma_db"),
    "DOCS_PATH": os.getenv("DOCS_PATH", "./data/f22/raw"),
    "PROCESSED_PATH": os.getenv("PROCESSED_PATH", "./data/f22/processed"),
}


def main():
    docs_path = Path(ENV["DOCS_PATH"])
    processed_path = Path(ENV["PROCESSED_PATH"])
    processed_path.mkdir(parents=True, exist_ok=True)

    if not docs_path.exists():
        print(f"[ERROR] No existe la carpeta: {docs_path}")
        sys.exit(1)

    files = [
        f for f in docs_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"[WARN] No se encontraron documentos soportados en {docs_path}")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  F22 Ingestión — {len(files)} archivos encontrados")
    print(f"{'='*60}\n")

    start_total = time.time()
    total_docs = 0
    total_chunks = 0
    all_chunks = []

    for i, file_path in enumerate(sorted(files), 1):
        print(f"[{i}/{len(files)}] {file_path.name}")
        extracted = extract_file(str(file_path))
        if extracted is None:
            continue

        # Save processed text
        out_file = processed_path / (file_path.stem + ".txt")
        out_file.write_text(extracted["content"], encoding="utf-8")

        chunks = chunk_document(extracted)
        all_chunks.extend(chunks)
        total_docs += 1
        total_chunks += len(chunks)
        print(f"  -> {len(chunks)} chunks generados\n")

    # Embed all chunks
    if all_chunks:
        print(f"\n[Embeddings] Enviando {total_chunks} chunks a ChromaDB...")
        embed_and_store(all_chunks, ENV)

    elapsed = time.time() - start_total
    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"  Documentos procesados : {total_docs}")
    print(f"  Chunks indexados      : {total_chunks}")
    print(f"  Tiempo total          : {elapsed:.1f}s")
    print(f"{'='*60}\n")

    # Verify
    import chromadb as _chroma
    client = _chroma.PersistentClient(path=ENV["CHROMA_PATH"])
    try:
        col = client.get_collection("f22_knowledge_base")
        print(f"  Verificacion ChromaDB : {col.count()} chunks almacenados")
        if col.count() > 0:
            print("  Estado: OK - Ingestión exitosa\n")
        else:
            print("  Estado: WARN - La coleccion existe pero esta vacía\n")
    except Exception as e:
        print(f"  Estado: ERROR - {e}\n")


if __name__ == "__main__":
    main()
