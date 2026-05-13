import json
import logging
import re
import time
from collections import defaultdict

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from backend.api.models import ChatRequest, ChatResponse
from backend.rag.pipeline import run_rag, stream_rag
from backend.rag.security import (
    UNSAFE_OUTPUT_REPLACEMENT,
    check_message,
    check_output,
    get_block_message,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Historial de sesiones en memoria (session_id → lista de turnos)
_sessions: dict[str, list[dict]] = defaultdict(list)

# Contador de intentos bloqueados por sesion. Tras 3 strikes consecutivos,
# se limpia el historial para evitar buildup multi-turn de ataques.
_blocked_strikes: dict[str, int] = defaultdict(int)
_STRIKES_RESET_THRESHOLD = 3


def sanitize_message(msg: str) -> str:
    msg = re.sub(r'[\x00-\x1F\x7F]', '', msg)
    return msg.strip()


def _stream_text_as_tokens(text: str):
    """Helper: convierte un texto fijo en eventos SSE compatibles con el frontend."""
    yield f"data: {json.dumps({'type': 'sources', 'sources': []}, ensure_ascii=False)}\n\n"
    for word in text.split(" "):
        yield f"data: {json.dumps({'type': 'token', 'content': word + ' '}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'done', 'related_questions': []}, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Endpoint principal — responde en streaming (SSE).

    Aplica defensas de seguridad antes y despues del LLM:
      1. check_message: bloquea jailbreaks, exfiltracion, prompt-leak, etc.
      2. stream_rag: pipeline normal RAG.
      3. check_output: si la respuesta filtro el system prompt o topicos peligrosos,
         reemplaza por mensaje seguro.

    Tras 3 strikes consecutivos en la misma sesion, limpia el historial para
    cortar ataques multi-turn.
    """
    safe_message = sanitize_message(request.message)
    session_id = request.session_id or "default"

    # ── Defensa de entrada ────────────────────────────────────────────────
    blocked, category, pattern = check_message(safe_message, session_id=session_id)
    if blocked:
        _blocked_strikes[session_id] += 1
        if _blocked_strikes[session_id] >= _STRIKES_RESET_THRESHOLD:
            _sessions.pop(session_id, None)
            logger.warning(
                "security_session_reset | session=%s | strikes=%d",
                session_id, _blocked_strikes[session_id],
            )
            _blocked_strikes[session_id] = 0

        block_msg = get_block_message(category)

        def reject_gen():
            yield from _stream_text_as_tokens(block_msg)

        return StreamingResponse(
            reject_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Mensaje OK → reseteamos contador de strikes
    _blocked_strikes[session_id] = 0
    history = _sessions[session_id]

    async def generate():
        full_answer = ""
        try:
            async for event in stream_rag(safe_message, history):
                if event["type"] == "token":
                    full_answer += event["content"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            msg = (
                "Límite de consultas alcanzado. Por favor espera unos minutos e intenta nuevamente."
                if "rate_limit" in str(e).lower() or "429" in str(e)
                else "Error al procesar la consulta. Intenta nuevamente."
            )
            yield f"data: {json.dumps({'type': 'error', 'content': msg})}\n\n"
            return

        # ── Defensa de salida ─────────────────────────────────────────────
        unsafe, _reason = check_output(full_answer, session_id=session_id)
        if unsafe:
            # No podemos un-stream los tokens. Usamos el evento 'error' que el
            # frontend ya maneja: reescribe la burbuja con UNSAFE_OUTPUT_REPLACEMENT
            # y limpia fuentes/preguntas relacionadas. Tambien sobreescribimos
            # full_answer en el historial para no contaminar turnos siguientes.
            full_answer = UNSAFE_OUTPUT_REPLACEMENT
            yield (
                "data: "
                + json.dumps(
                    {"type": "error", "content": UNSAFE_OUTPUT_REPLACEMENT},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        # Guardar en historial solo cuando la respuesta está completa y validada
        if full_answer:
            _sessions[session_id].append(
                {"human": request.message, "ai": full_answer}
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx no almacena en buffer el stream
        },
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint de compatibilidad — respuesta completa (no streaming)."""
    start = time.time()
    safe_message = sanitize_message(request.message)
    session_id = request.session_id or "default"

    # Defensa de entrada
    blocked, category, _pattern = check_message(safe_message, session_id=session_id)
    if blocked:
        _blocked_strikes[session_id] += 1
        if _blocked_strikes[session_id] >= _STRIKES_RESET_THRESHOLD:
            _sessions.pop(session_id, None)
            _blocked_strikes[session_id] = 0
        return JSONResponse(
            content=ChatResponse(
                answer=get_block_message(category),
                sources=[],
                session_id=session_id,
                related_questions=[],
            ).model_dump()
        )

    _blocked_strikes[session_id] = 0

    try:
        result = run_rag(safe_message, _sessions[session_id])
    except RuntimeError:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Error al procesar la consulta. Intenta nuevamente.")
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

    # Defensa de salida
    unsafe, _reason = check_output(result["answer"], session_id=session_id)
    answer = UNSAFE_OUTPUT_REPLACEMENT if unsafe else result["answer"]

    _sessions[session_id].append({"human": request.message, "ai": answer})

    elapsed_ms = int((time.time() - start) * 1000)
    response = ChatResponse(
        answer=answer,
        sources=result["sources"] if not unsafe else [],
        session_id=session_id,
        related_questions=result.get("related_questions", []) if not unsafe else [],
    )
    return JSONResponse(
        content=response.model_dump(),
        headers={"X-Response-Time": f"{elapsed_ms}ms"},
    )
