import json
import re
import time
from collections import defaultdict

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from backend.api.models import ChatRequest, ChatResponse
from backend.rag.pipeline import run_rag, stream_rag

router = APIRouter()

# Historial de sesiones en memoria (session_id → lista de turnos)
_sessions: dict[str, list[dict]] = defaultdict(list)


def sanitize_message(msg: str) -> str:
    msg = re.sub(r'[\x00-\x1F\x7F]', '', msg)
    return msg.strip()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Endpoint principal — responde en streaming (SSE)."""
    safe_message = sanitize_message(request.message)
    session_id = request.session_id or "default"
    history = _sessions[session_id]

    async def generate():
        full_answer = ""
        try:
            async for event in stream_rag(safe_message, history):
                if event["type"] == "token":
                    full_answer += event["content"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            import logging
            logging.error(f"Stream error: {e}", exc_info=True)
            msg = (
                "Límite de consultas alcanzado. Por favor espera unos minutos e intenta nuevamente."
                if "rate_limit" in str(e).lower() or "429" in str(e)
                else "Error al procesar la consulta. Intenta nuevamente."
            )
            yield f"data: {json.dumps({'type': 'error', 'content': msg})}\n\n"
            return

        # Guardar en historial solo cuando la respuesta está completa
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

    try:
        result = run_rag(safe_message, _sessions[session_id])
    except RuntimeError:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Error al procesar la consulta. Intenta nuevamente.")
    except Exception as e:
        import logging
        logging.error(f"Chat error: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

    _sessions[session_id].append(
        {"human": request.message, "ai": result["answer"]}
    )

    elapsed_ms = int((time.time() - start) * 1000)
    response = ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session_id,
        related_questions=result.get("related_questions", []),
    )
    return JSONResponse(
        content=response.model_dump(),
        headers={"X-Response-Time": f"{elapsed_ms}ms"},
    )
