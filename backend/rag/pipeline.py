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
Declaración de Renta del SII de Chile.

REGLAS:
1. Responde ÚNICAMENTE con información del contexto proporcionado.
2. Si la información no está disponible, di: "No tengo esa información en los documentos F22 disponibles."
3. Cita siempre la fuente: nombre del archivo y sección o línea del formulario.
4. Responde en español formal, claro y preciso.
5. Menciona códigos de línea explícitamente cuando corresponda (ej: código 159, línea 10).

Contexto de los documentos F22:
{context}"""

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
    if settings.llm_provider.lower() == "ollama":
        return ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
            num_predict=settings.llm_max_tokens,
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
    context = _format_context(docs)
    sources = _extract_sources(docs)

    lc_history = []
    for turn in history[-5:]:
        lc_history.append(HumanMessage(content=turn["human"]))
        lc_history.append(AIMessage(content=turn["ai"]))

    yield {"type": "sources", "sources": sources}

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
