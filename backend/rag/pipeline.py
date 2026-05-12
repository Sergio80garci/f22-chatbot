from functools import lru_cache
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from backend.config import settings
from backend.rag.retriever import retrieve

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
    """Basándote en la respuesta del asistente (70%) y la intención del usuario (30%), \
genera 3 preguntas de seguimiento sobre el Formulario 22 del SII de Chile. \
Sin numeración, una por línea, cada una termina con (?).

Usuario: {question}
Asistente: {answer}

Preguntas:"""
)


@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_tokens=2048,
    )


def _build_llm() -> ChatGroq:
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


def _parse_related(raw: str) -> list[str]:
    return [
        line.strip()
        for line in raw.strip().split("\n")
        if line.strip() and "?" in line
    ][:3]


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
        related_chain = _RELATED_PROMPT | llm
        related_response = await related_chain.ainvoke({
            "question": question[:200],
            "answer": full_answer[:800],
        })
        related_questions = _parse_related(related_response.content)
    except Exception:
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
            "answer": response.content[:800],
        })
        related_questions = _parse_related(related_response.content)
    except Exception:
        related_questions = []

    return {
        "answer": response.content,
        "sources": sources,
        "related_questions": related_questions,
    }
