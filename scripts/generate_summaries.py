"""
Genera y cachea los resúmenes de todos los documentos indexados.
Uso: python scripts/generate_summaries.py
Solo necesita correrse UNA VEZ — guarda resultados en data/summaries_cache.json
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_core.messages import HumanMessage

from backend.config import settings
from backend.rag.pipeline import _build_llm

CACHE_FILE = Path("data/summaries_cache.json")
DELAY = 3  # segundos entre llamadas para no exceder rate limit


def load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    col = client.get_collection(settings.chroma_collection)
    data = col.get(include=["metadatas", "documents"])

    # Agrupar chunks por documento
    docs: dict[str, list[str]] = {}
    for meta, doc in zip(data["metadatas"], data["documents"]):
        fname = meta.get("filename", meta.get("source", "unknown"))
        docs.setdefault(fname, []).append(doc)

    cache = load_cache()
    pending = [f for f in docs if not cache.get(f)]

    print(f"\nDocumentos totales : {len(docs)}")
    print(f"Ya en cache        : {len(docs) - len(pending)}")
    print(f"Por generar        : {len(pending)}")
    print(f"Tiempo estimado    : ~{len(pending) * DELAY // 60} min {len(pending) * DELAY % 60} seg\n")

    if not pending:
        print("Todo está en cache. Nada que hacer.")
        return

    llm = _build_llm()

    for i, fname in enumerate(pending, 1):
        chunks = docs[fname][:2]
        content = "\n\n".join(chunks)
        print(f"[{i}/{len(pending)}] {fname[:60]}...", end=" ", flush=True)
        try:
            response = llm.invoke([HumanMessage(
                content=f"Resume en 2 líneas máximo el siguiente contenido del documento F22:\n\n{content}"
            )])
            cache[fname] = response.content.strip()
            save_cache(cache)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            cache[fname] = ""
        if i < len(pending):
            time.sleep(DELAY)

    ok = sum(1 for f in pending if cache.get(f))
    print(f"\nCompletado: {ok}/{len(pending)} resúmenes generados.")
    print(f"Cache guardado en: {CACHE_FILE}\n")


if __name__ == "__main__":
    main()
