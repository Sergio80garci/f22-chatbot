import time
import re
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.api.models import ChatRequest, ChatResponse
from backend.rag.pipeline import run_rag


def sanitize_message(msg: str) -> str:
    """Sanitize user message to prevent prompt injection."""
    # Remove potential injection patterns
    msg = re.sub(r'[\x00-\x1F\x7F]', '', msg)  # Remove control characters
    msg = msg.replace('\\', '').replace('"', '\"')  # Escape dangerous chars
    return msg.strip()

router = APIRouter()

# In-memory conversation history: session_id -> list of {human, ai} dicts
_sessions: dict[str, list[dict]] = defaultdict(list)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start = time.time()

    try:
        # Sanitize input to prevent injection
        safe_message = sanitize_message(request.message)
        result = run_rag(safe_message, _sessions[request.session_id])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Error al procesar la consulta. Intenta nuevamente.")
    except Exception as e:
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Servicio LLM no disponible. Intenta en unos momentos.",
            )
        # Log the actual error internally, but don't expose it to client
        import logging
        logging.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor. Por favor intenta nuevamente.")

    _sessions[request.session_id].append(
        {"human": request.message, "ai": result["answer"]}
    )

    elapsed_ms = int((time.time() - start) * 1000)
    response = ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=request.session_id,
        related_questions=result.get("related_questions", []),
    )
    headers = {"X-Response-Time": f"{elapsed_ms}ms"}
    return JSONResponse(content=response.model_dump(), headers=headers)
