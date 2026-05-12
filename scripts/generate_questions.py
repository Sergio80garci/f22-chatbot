"""
Genera 3 preguntas por documento desde ChromaDB, valida que el RAG pueda responderlas,
y guarda solo las válidas en data/questions_pool.json
Uso: python scripts/generate_questions.py
"""
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_core.messages import HumanMessage

from backend.config import settings
from backend.rag.pipeline import _build_llm, run_rag

QUESTIONS_FILE = Path("data/questions_pool.json")
QUESTIONS_PER_DOC = 3
DELAY = 4
NO_ANSWER_PHRASES = [
    "no tengo esa información",
    "no se menciona",
    "no está disponible",
    "no puedo responder",
    "no hay información",
    "no encuentro",
]

INTERNAL_REF_PATTERNS = [
    r'c[oó]digo\s+\d+',
    r'l[íi]nea\s+\d+',
    r'recuadro\s+n[°o]',
    r'art[íi]culo\s+\d+',
    r'n[°o]\s*\d+',
    r'letra\s+[a-z]\)',
    r'inciso\s+\d+',
    r'dj\s+f-\d+',
    r'circular\s+n[°o]',
    r'f-\d{4}',
    r'certificado\s+modelo',
    r'\d{4}\s+del\s+f',
]


def clean_question(line: str) -> str:
    line = line.strip()
    line = re.sub(r'^[\d]+[.)]\s*', '', line)
    line = re.sub(r'^[-•]\s*', '', line)
    return line.strip()


def has_internal_ref(q: str) -> bool:
    q_lower = q.lower()
    return any(re.search(p, q_lower) for p in INTERNAL_REF_PATTERNS)


def rag_can_answer(question: str) -> bool:
    """Retorna True si el RAG puede responder la pregunta (no responde 'no tengo información')."""
    try:
        result = run_rag(question, [])
        answer = result.get("answer", "").lower()
        return not any(phrase in answer for phrase in NO_ANSWER_PHRASES)
    except Exception:
        return False


def load_existing() -> dict[str, list[str]]:
    try:
        data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def save_progress(by_doc: dict[str, list[str]]) -> None:
    QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUESTIONS_FILE.write_text(json.dumps(by_doc, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    col = client.get_collection(settings.chroma_collection)
    data = col.get(include=["metadatas", "documents"])

    docs: dict[str, list[str]] = defaultdict(list)
    for meta, doc in zip(data["metadatas"], data["documents"]):
        fname = meta.get("filename", meta.get("source", "unknown"))
        docs[fname].append(doc)

    by_doc = load_existing()
    pending = [f for f in sorted(docs.keys()) if f not in by_doc]

    total_q = sum(len(v) for v in by_doc.values())
    print(f"\nDocumentos totales  : {len(docs)}")
    print(f"Ya procesados       : {len(by_doc)}")
    print(f"Por procesar        : {len(pending)}")
    print(f"Preguntas en pool   : {total_q}\n")

    if not pending:
        print("Todos los documentos ya tienen preguntas.")
        print(f"Pool total: {total_q} preguntas listas.")
        return

    llm = _build_llm()

    for i, fname in enumerate(pending, 1):
        chunks = docs[fname][:3]
        content = "\n\n".join(chunks)
        print(f"[{i}/{len(pending)}] {fname[:50]:<50}", end=" ", flush=True)

        try:
            response = llm.invoke([HumanMessage(content=f"""Eres un experto en el Formulario 22 (F22) de Declaración Anual de Impuesto a la Renta del SII de Chile.

Basándote en el siguiente contenido, genera exactamente {QUESTIONS_PER_DOC} preguntas que un contribuyente chileno le haría a un asistente virtual.

Requisitos ESTRICTOS:
- PROHIBIDO mencionar: números de código, línea, recuadro, artículo, inciso, archivo, declaración jurada, circular
- Lenguaje cotidiano: "¿Cómo declaro...?", "¿Qué es...?", "¿Cuándo debo...?", "¿Puedo rebajar...?", "¿Quiénes tienen derecho a...?"
- Conceptos permitidos: honorarios, rentas, créditos, impuestos, deducciones, plazos, devoluciones, cotizaciones, donaciones, bienes raíces
- Sin numeración ni guiones al inicio
- Una por línea, termina con (?)

Contenido:
{content}

Preguntas:""")])

            candidates = [
                clean_question(line)
                for line in response.content.split('\n')
                if line.strip() and '?' in line and not has_internal_ref(line)
            ][:QUESTIONS_PER_DOC]

            # Validar contra RAG
            valid = []
            for q in candidates:
                if rag_can_answer(q):
                    valid.append(q)
                time.sleep(2)

            if valid:
                by_doc[fname] = valid
                save_progress(by_doc)
                print(f"OK ({len(valid)}/{len(candidates)} válidas)")
            else:
                print(f"SKIP (0/{len(candidates)} válidas)")

        except Exception as e:
            print(f"ERROR: {e}")

        if i < len(pending):
            time.sleep(DELAY)

    flat = [q for qs in by_doc.values() for q in qs]
    print(f"\n{'='*60}")
    print(f"  Documentos con preguntas: {len(by_doc)}")
    print(f"  Preguntas válidas       : {len(flat)}")
    print(f"  Archivo                 : {QUESTIONS_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
