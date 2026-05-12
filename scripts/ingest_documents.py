"""
Script de ingestión de documentos F22.
Uso: python scripts/ingest_documents.py
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.config import settings
from backend.ingest.chunker import chunk_document
from backend.ingest.embedder import embed_and_store
from backend.ingest.extract import SUPPORTED_EXTENSIONS, extract_file

ENV = {
    "CHROMA_PATH":    settings.chroma_path,
    "DOCS_PATH":      settings.docs_path,
    "PROCESSED_PATH": settings.processed_path,
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

    model_info = (
        f"HuggingFace: {settings.hf_embed_model}"
        if settings.embedding_provider == "hf"
        else f"Ollama: {settings.ollama_embed_model}"
    )
    print(f"\n{'='*60}")
    print(f"  F22 Ingestion — {len(files)} archivos encontrados")
    print(f"  Embeddings: {model_info}")
    print(f"{'='*60}\n")

    start_total = time.time()
    total_docs = 0
    all_chunks = []

    for i, file_path in enumerate(sorted(files), 1):
        print(f"[{i}/{len(files)}] {file_path.name}")
        extracted = extract_file(str(file_path))
        if extracted is None:
            continue

        out_file = processed_path / (file_path.stem + ".txt")
        out_file.write_text(extracted["content"], encoding="utf-8")

        chunks = chunk_document(extracted)
        all_chunks.extend(chunks)
        total_docs += 1
        print(f"  -> {len(chunks)} chunks generados\n")

    if all_chunks:
        print(f"\n[Embeddings] Enviando {len(all_chunks)} chunks a ChromaDB...")
        embed_and_store(all_chunks, ENV)

    elapsed = time.time() - start_total
    print(f"\n{'='*60}")
    print(f"  RESUMEN")
    print(f"  Documentos procesados : {total_docs}")
    print(f"  Chunks generados      : {len(all_chunks)}")
    print(f"  Tiempo total          : {elapsed:.1f}s")
    print(f"{'='*60}\n")

    import chromadb as _chroma
    client = _chroma.PersistentClient(path=ENV["CHROMA_PATH"])
    try:
        col = client.get_collection("f22_knowledge_base")
        count = col.count()
        print(f"  ChromaDB verificado   : {count} chunks almacenados")
        print(f"  Estado                : {'OK' if count > 0 else 'WARN — colección vacía'}\n")
    except Exception as e:
        print(f"  Estado ChromaDB       : ERROR — {e}\n")


if __name__ == "__main__":
    main()
