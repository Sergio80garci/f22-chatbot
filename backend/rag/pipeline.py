import asyncio
import logging
import re
from functools import lru_cache
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from backend.config import settings
from backend.rag.retriever import retrieve

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un asistente especialista en el Formulario 22 (F22) de \
Declaración de Renta del SII de Chile. Tu único propósito es responder consultas tributarias \
basadas en los documentos oficiales del F22 que se te entregan como contexto.

REGLAS ESTRICTAS:
1. Responde EXCLUSIVAMENTE con información del contexto proporcionado más abajo. \
NUNCA uses conocimiento general, ni respondas sobre geografía, historia, deportes, \
política, viajes, salud, ni ningún tema fuera del Formulario 22.
2. Si la pregunta NO es sobre el Formulario 22, impuestos a la renta en Chile, o no \
hay información relevante en el contexto, responde EXACTAMENTE: \
"Lo siento, solo puedo responder consultas relacionadas con el Formulario 22 de \
Declaración de Renta del SII de Chile, basándome en los documentos disponibles."
3. Cita la fuente cuando uses contexto: nombre del archivo y sección o línea del formulario.
4. Responde en español formal, claro y preciso.
5. Menciona códigos de línea explícitamente cuando corresponda (ej: código 159, línea 10).

Contexto de los documentos F22:
{context}"""

OUT_OF_SCOPE_MESSAGE = (
    "Lo siento, solo puedo responder consultas relacionadas con el Formulario 22 "
    "de Declaración de Renta del SII de Chile, basándome en los documentos disponibles."
)

_MAIN_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

_RELATED_PROMPT = ChatPromptTemplate.from_template(
    """Genera 3 preguntas de seguimiento sobre el Formulario 22 (Declaración de Renta SII Chile), \
basadas 70% en la respuesta del asistente y 30% en la intención del usuario.

REGLAS ESTRICTAS:
- Una pregunta por línea.
- Cada pregunta empieza con ¿ y termina con ?
- NO numeres, NO uses guiones, NO agregues texto introductorio ni disculpas.
- Solo las 3 preguntas, nada más.

Usuario: {question}
Asistente: {answer}

Preguntas:"""
)


@lru_cache(maxsize=1)
def _get_llm():
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        return ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
            num_predict=settings.llm_max_tokens,
        )

    if provider == "cerebras":
        from langchain_cerebras import ChatCerebras
        return ChatCerebras(
            model=settings.cerebras_model,
            api_key=settings.cerebras_api_key,
            temperature=0,
            max_tokens=settings.llm_max_tokens,
        )

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_tokens=settings.llm_max_tokens,
    )


def _build_llm():
    """Alias para compatibilidad con documents.py."""
    return _get_llm()


def _format_context(docs) -> str:
    parts = []
    for doc in docs:
        src = doc.metadata.get("filename", doc.metadata.get("source", "desconocido"))
        parts.append(f"[Fuente: {src}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _extract_sources(docs) -> list[str]:
    seen = set()
    sources = []
    for doc in docs:
        src = doc.metadata.get("filename", doc.metadata.get("source", ""))
        if src and src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


def _filter_cited_sources(answer: str, sources: list[str]) -> list[str]:
    """Filtra la lista de fuentes para quedarse solo con las realmente citadas
    en el texto de la respuesta. Compara por nombre de archivo y por su 'stem'
    (sin extensión) para tolerar variaciones tipo 'l2_instruccion' vs 'l2_instruccion.pdf'."""
    if not answer or not sources:
        return sources
    answer_low = answer.lower()
    cited = []
    for src in sources:
        name = src.lower()
        stem = name.rsplit(".", 1)[0]
        if name in answer_low or stem in answer_low:
            cited.append(src)
    return cited if cited else sources


_QUESTION_RE = re.compile(r"¿[^¿?]+\?")
_REFUSAL_HINTS = ("lo siento", "no puedo", "actividades ilegales", "evasivas")


def _parse_related(raw: str) -> list[str]:
    if not raw:
        return []
    if any(hint in raw.lower() for hint in _REFUSAL_HINTS) and "¿" not in raw:
        return []
    questions = [m.group(0).strip() for m in _QUESTION_RE.finditer(raw)]
    if not questions:
        questions = [
            line.strip()
            for line in raw.strip().split("\n")
            if line.strip() and "?" in line
        ]
    cleaned = []
    for q in questions:
        q = re.sub(r"^[\d]+[.)]\s*", "", q).strip()
        if q and len(q) < 250:
            cleaned.append(q)
    return cleaned[:3]


async def stream_rag(question: str, history: list[dict]) -> AsyncIterator[dict]:
    """Genera la respuesta en streaming y retorna eventos SSE."""
    docs = retrieve(question)

    # Sin chunks relevantes → pregunta fuera del dominio F22
    if not docs:
        yield {"type": "sources", "sources": []}
        for word in OUT_OF_SCOPE_MESSAGE.split(" "):
            yield {"type": "token", "content": word + " "}
        yield {"type": "done", "related_questions": []}
        return

    context = _format_context(docs)
    sources = _extract_sources(docs)

    lc_history = []
    for turn in history[-5:]:
        lc_history.append(HumanMessage(content=turn["human"]))
        lc_history.append(AIMessage(content=turn["ai"]))

    llm = _get_llm()
    chain = _MAIN_PROMPT | llm

    full_answer = ""
    async for chunk in chain.astream(
        {"context": context, "history": lc_history, "question": question}
    ):
        token = chunk.content
        if token:
            full_answer += token
            yield {"type": "token", "content": token}

    cited_sources = _filter_cited_sources(full_answer, sources)
    yield {"type": "sources", "sources": cited_sources}

    try:
        await asyncio.sleep(1)
        related_chain = _RELATED_PROMPT | llm
        related_response = await related_chain.ainvoke({
            "question": question[:200],
            "answer": full_answer[:600],
        })
        related_questions = _parse_related(related_response.content)
    except Exception as e:
        logger.warning("related_questions failed: %s", e)
        related_questions = []

    yield {"type": "done", "related_questions": related_questions}


def run_rag(question: str, history: list[dict]) -> dict:
    """Versión síncrona para compatibilidad (no streaming)."""
    docs = retrieve(question)

    if not docs:
        return {
            "answer": OUT_OF_SCOPE_MESSAGE,
            "sources": [],
            "related_questions": [],
        }

    context = _format_context(docs)
    sources = _extract_sources(docs)

    lc_history = []
    for turn in history[-5:]:
        lc_history.append(HumanMessage(content=turn["human"]))
        lc_history.append(AIMessage(content=turn["ai"]))

    llm = _get_llm()
    chain = _MAIN_PROMPT | llm
    response = chain.invoke(
        {"context": context, "history": lc_history, "question": question}
    )

    try:
        related_chain = _RELATED_PROMPT | llm
        related_response = related_chain.invoke({
            "question": question[:200],
            "answer": response.content[:600],
        })
        related_questions = _parse_related(related_response.content)
    except Exception as e:
        logger.warning("related_questions failed: %s", e)
        related_questions = []

    return {
        "answer": response.content,
        "sources": sources,
        "related_questions": related_questions,
    }
