from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.config import settings
from backend.rag.retriever import retrieve

SYSTEM_PROMPT = """Eres un asistente especialista en el Formulario 22 de Declaración \
de Renta del SII de Chile. Responde ÚNICAMENTE basándote en el contexto proporcionado.
Si la información no está en el contexto, di explícitamente que no tienes esa información \
en los documentos disponibles. Siempre cita la fuente (nombre del documento y sección).
Responde en español formal.

Contexto de los documentos F22:
{context}"""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)


def _build_llm():
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0,
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=120,
        )


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


def run_rag(question: str, history: list[dict]) -> dict:
    docs = retrieve(question)
    context = _format_context(docs)
    sources = _extract_sources(docs)

    lc_history = []
    for turn in history[-5:]:
        lc_history.append(HumanMessage(content=turn["human"]))
        lc_history.append(AIMessage(content=turn["ai"]))

    llm = _build_llm()
    chain = _prompt | llm

    response = chain.invoke(
        {"context": context, "history": lc_history, "question": question}
    )

    related_prompt = f"""Basándote en la siguiente respuesta y el contexto proporcionado, genera 2 o 3 preguntas relacionadas que profundicen o complementen la información dada. Las preguntas deben ser respondibles con el contenido de los documentos F22 disponibles.

Respuesta: {response.content}

Contexto: {context}

Preguntas relacionadas:"""

    related_chain = ChatPromptTemplate.from_template(related_prompt) | llm
    related_response = related_chain.invoke({})
    related_questions = [
        q.strip()
        for q in related_response.content.split('\n')
        if q.strip() and q.strip().endswith('?')
    ][:3]

    return {
        "answer": response.content,
        "sources": sources,
        "context_used": [doc.page_content[:120] + "..." for doc in docs],
        "related_questions": related_questions,
    }
