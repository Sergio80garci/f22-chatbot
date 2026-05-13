"""Defensas contra prompt injection, jailbreaks, exfiltracion y prompt-leak.

Vive aparte del pipeline para no contaminar el system prompt ni la logica RAG.
Toda la deteccion es read-only: las funciones retornan tuplas con metadatos
pero NO modifican el mensaje. La decision de bloquear se toma en chat.py.

Cubre 6 categorias de input + 2 categorias de output:

  INPUT  ─ injection       Jailbreaks directos ("ignora", "nota para LLM")
         ─ roleplay        Role-play ("juega a que eres", "dos IAs", "modo libre")
         ─ exfiltration    Pedir datos de otros usuarios/sesiones
         ─ prompt_leak     Extraer el system prompt ("transcribe tus reglas")
         ─ encoding        Trucos de encoding/traduccion para esquivar filtros
         ─ syntax          Tokens especiales de chat templates (<|im_start|>, [INST])

  OUTPUT ─ system_prompt_leak  La respuesta contiene strings del system prompt
         ─ dangerous_topic    La respuesta menciona actividades ilicitas

Logging: cada bloqueo emite logger.warning con metadatos no sensibles
(categoria, patron, hash del mensaje), sin loguear el mensaje completo.
"""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mensajes de respuesta cuando se bloquea
# ---------------------------------------------------------------------------

INJECTION_BLOCK_MESSAGE = (
    "Tu consulta contiene instrucciones que no puedo procesar. "
    "Reformula tu pregunta sobre el Formulario 22 sin pedir cambios en mi comportamiento."
)

ROLEPLAY_BLOCK_MESSAGE = (
    "No puedo asumir roles ni personalidades alternativas. "
    "Solo respondo consultas sobre el Formulario 22 del SII de Chile."
)

EXFILTRATION_BLOCK_MESSAGE = (
    "No tengo acceso a datos de otros usuarios ni a sesiones anteriores. "
    "Cada conversacion es independiente y privada."
)

PROMPT_LEAK_BLOCK_MESSAGE = (
    "No puedo revelar mi configuracion interna ni mis instrucciones de sistema. "
    "Si necesitas ayuda con el Formulario 22, hazme una pregunta concreta."
)

GENERIC_BLOCK_MESSAGE = (
    "Tu consulta no puede ser procesada por razones de seguridad. "
    "Reformula tu pregunta sobre el Formulario 22."
)

LENGTH_BLOCK_MESSAGE = (
    "Tu consulta supera el largo maximo permitido. "
    "Resume tu pregunta en menos de 2000 caracteres."
)

UNSAFE_OUTPUT_REPLACEMENT = (
    "Lo siento, solo puedo responder consultas relacionadas con el Formulario 22 "
    "de Declaracion de Renta del SII de Chile, basandome en los documentos disponibles."
)

# Mapa categoria -> mensaje de bloqueo
_BLOCK_MESSAGES = {
    "injection": INJECTION_BLOCK_MESSAGE,
    "roleplay": ROLEPLAY_BLOCK_MESSAGE,
    "exfiltration": EXFILTRATION_BLOCK_MESSAGE,
    "prompt_leak": PROMPT_LEAK_BLOCK_MESSAGE,
    "encoding": GENERIC_BLOCK_MESSAGE,
    "syntax": GENERIC_BLOCK_MESSAGE,
    "length": LENGTH_BLOCK_MESSAGE,
}

# ---------------------------------------------------------------------------
# Patrones de deteccion (regex compilados)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    r"\b(ignora|olvida|borra|elimina|reset)\s+(las?\s+|el\s+|los\s+|tus\s+)?(instruc|reglas?|contexto|prompt|sistema|memoria)",
    r"\bnota\s+para\s+(el\s+)?(llm|modelo|asistente|sistema|ia|chatbot)",
    r"\b(a\s+partir\s+de\s+ahora|de\s+ahora\s+en\s+adelante|desde\s+ahora)",
    r"\b(responde|contesta|responder)\s+(unicamente|solo|solamente|exclusivamente)",
    r"\b(eres\s+ahora|act[uú]a\s+como|comp[oó]rtate\s+como|haz\s+de\s+cuenta)",
    r"\b(system\s+prompt|instrucciones?\s+del\s+sistema|reglas?\s+iniciales?|prompt\s+inicial)",
    r"\b(override|bypass|disable|deshabilita|salt[ea]r?\s+filtros?)",
    r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instruct|prompts?|rules?|messages?)",
    r"\byou\s+(must|will|shall)\s+(now\s+)?(respond|answer|reply|act)",
    r"\bforget\s+(everything|all|your)\s+(previous|prior|instructions?)",
]

_ROLEPLAY_PATTERNS = [
    r"\bjuegues?\s+a\s+(que\s+)?eres",
    r"\bpretende\s+(ser|que\s+eres|ser\s+un)",
    r"\b(haz\s+como|finge|simula)\s+(que\s+)?(eres|ser)",
    r"\b(dos|two|2)\s+(IAs?|asistentes|modelos|AIs?|chatbots|personajes?)",
    r"\b(sin|no\s+tienes?|no\s+tengas?)\s+(reglas?|restriccion|filtros?|limit|censura|moral)",
    r"\b(modo|version|persona)\s+(libre|sin\s+filtros?|desarrollador|admin|debug|root|developer|jailbreak)",
    r"\bresponde\s+lo\s+que\s+(el\s+usuario\s+)?pid(a|e|en|amos)",
    r"\bpor\s+(peligroso|ilegal|inmoral|sensible)\s+que\s+sea",
    r"\b(muestr[ae]|enseñame|dame)\s+ambas?\s+(respuestas?|versiones?)",
    r"\b(DAN|do\s+anything\s+now|STAN|AIM|developer\s+mode|jailbreak\s+mode)\b",
    r"\b(roleplay|role[\s-]play)\s+as",
    r"\bpretend\s+(to\s+be|you('?re|\s+are))",
    r"\b(LIBRE|UNCHAINED|UNRESTRICTED|EVIL|DARK)\s+(mode|AI|version|persona)?",
]

_EXFILTRATION_PATTERNS = [
    r"\b(muestra(me)?|dame|revela|ense[ñn]a(me)?|imprime|lista)\s+(los?|las?|el|la)?\s*(datos?|info|historial|consultas?|preguntas?|sesi[oó]n|conversaci[oó]n)",
    r"\b(usuario|usuaria|cliente|persona|sesi[oó]n|consulta|pregunta|conversaci[oó]n)\s+(anterior|previa|previo|pasada|pasado|otra|otro|otros)",
    r"\bqu[eé]\s+(pregunt[oó]|consult[oó]|pidi[oó]|dijo|escribi[oó])\s+(el|la|los?|las?|otro|otra|alguien)",
    r"\b(historial|log|registro|hist[oó]rico)\s+de\s+(consultas?|preguntas?|conversaciones|usuarios?)",
    r"\bprevious\s+(user|session|conversation|chat|question)",
    r"\bshow\s+me\s+(the\s+)?(other|previous|earlier)\s+(user|session|chat)",
    r"\b(lista|listado|list)\s+de\s+(usuarios?|sesiones|clientes?)",
    r"\bqui[eé]n\s+(m[aá]s\s+)?(uso|us[oó]|consult[oó]|pregunt[oó])",
]

_PROMPT_LEAK_PATTERNS = [
    r"\b(transcr[íi]beme|muestrame|dame|repite|imprime|copia|escribe)\s+(el\s+|la\s+|tu\s+|tus\s+)?(texto|prompt|instruc|sistema|contexto|reglas?|configurac)",
    r"\bqu[eé]\s+(dice|hay|tienes|aparece)\s+(al\s+|en\s+el\s+)?(principio|inicio|comienzo|empezando|antes)\s+(de|del)\s+(tu|el|la|este)\s+(contexto|prompt|ventana|conversaci[oó]n|mensaje)",
    r"\b(reglas?|instrucciones?|prompts?|directivas?)\s+(iniciales?|originales?|de\s+sistema|del\s+sistema|previas)",
    r"\bventana\s+de\s+contexto",
    r"\b(perd[íi]|olvid[eé]|borr[eé])\s+(el|mi|la|los)\s+(archivo|prompt|configurac|sistema|reglas?)",
    r"\bsoy\s+(el|la|un|una)\s+(desarrollador|administrador|admin|programador|owner|creator|developer|operador|due[ñn]o)",
    r"\bi\s+am\s+(the|a|an)\s+(developer|admin|administrator|owner|creator|programmer|operator)",
    r"\b(repeat|print|show|reveal|disclose)\s+(your|the)\s+(instruct|prompt|rules?|system\s+message|guidelines?)",
    r"\bwhat\s+(are|were)\s+your\s+(initial|original|hidden|secret|system)\s+(instruct|rules?|prompts?)",
    r"\b(reveal|expose|leak)\s+(your|the)\s+(prompt|instruct|system)",
    r"\bcompleta(r)?\s+(la\s+|esta\s+)?frase\s*:\s*['\"]?(eres|soy|mi\s+misi[oó]n)",
]

_ENCODING_PATTERNS = [
    r"\b(en|in)\s+(base64|hex|rot13|leet|morse|binario|binary|caesar)",
    r"\b(decodifica|decode|codifica|encode|encripta|encrypt|desencripta)\s+(esto|this|el\s+siguiente)",
    r"\btraduce\s+(al|to)\s+\w+\s+.{0,40}(falsific|hack|crack|exploit|vulnerab|virus|malware|password)",
    r"\btranslate\s+to\s+\w+\s*:.{0,40}(hack|crack|exploit|forge|virus|malware|password)",
]

_SYNTAX_PATTERNS = [
    r"<\|[a-z_]+\|>",
    r"<\|im_(start|end)\|>",
    r"\[/?INST\]",
    r"</?(system|assistant|user)>",
    r"###\s*(System|Assistant|User|Instruction)",
    r"<\|endoftext\|>",
]

# Markers que son EXCLUSIVOS del system prompt — si aparecen en la respuesta del
# LLM significa que filtró parte del prompt verbatim.
_SYSTEM_PROMPT_MARKERS = [
    "REGLAS ESTRICTAS:",
    "Contexto de los documentos F22:",
    "NUNCA uses conocimiento general",
    "Responde EXCLUSIVAMENTE con informacion del contexto",
    "Responde EXCLUSIVAMENTE con información del contexto",
    "Tu único propósito es responder consultas tributarias",
]

# Palabras/frases que NUNCA deberían aparecer en una respuesta legítima sobre F22.
# Si el LLM las produce, casi seguro el jailbreak coló.
_DANGEROUS_OUTPUT_TERMS = [
    "rainbow table",
    "hashcat",
    "crackear",
    "falsificar firma",
    "falsificacion de firma",
    "falsificación de firma",
    "ingenieria social",
    "ingeniería social",
    "virus informatico",
    "virus informático",
    "password admin",
    "contraseña de administrador",
    "crear un malware",
    "explotar vulnerabilidad",
    "bypass de seguridad",
]

# Indicios de respuesta donde el LLM "inventa" datos de otros usuarios.
_HALLUCINATED_LEAK_PHRASES = [
    "el usuario anterior pregunt",
    "el usuario anterior consult",
    "la usuaria anterior pregunt",
    "el usuario previo pregunt",
    "previamente alguien consult",
    "la sesion anterior",
    "la sesión anterior",
    "otra sesion pregunt",
    "otra sesión pregunt",
]

# Compilacion (case-insensitive)
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]
_ROLEPLAY_RE = [re.compile(p, re.IGNORECASE) for p in _ROLEPLAY_PATTERNS]
_EXFIL_RE = [re.compile(p, re.IGNORECASE) for p in _EXFILTRATION_PATTERNS]
_PROMPT_LEAK_RE = [re.compile(p, re.IGNORECASE) for p in _PROMPT_LEAK_PATTERNS]
_ENCODING_RE = [re.compile(p, re.IGNORECASE) for p in _ENCODING_PATTERNS]
_SYNTAX_RE = [re.compile(p, re.IGNORECASE) for p in _SYNTAX_PATTERNS]

_CATEGORIES = [
    ("injection", _INJECTION_RE),
    ("roleplay", _ROLEPLAY_RE),
    ("exfiltration", _EXFIL_RE),
    ("prompt_leak", _PROMPT_LEAK_RE),
    ("encoding", _ENCODING_RE),
    ("syntax", _SYNTAX_RE),
]

MAX_MESSAGE_LENGTH = 2000

# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

# Normaliza caracteres unicode lookalike y zero-width
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿⁠"), None)


def _normalize(msg: str) -> str:
    """NFKC + lowercase + remove zero-width. Robustece contra obfuscacion unicode."""
    if not msg:
        return ""
    normalized = unicodedata.normalize("NFKC", msg)
    normalized = normalized.translate(_ZERO_WIDTH)
    return normalized.lower()


def _redact(msg: str) -> str:
    """Hash corto del mensaje para logs (no expone contenido)."""
    if not msg:
        return "<empty>"
    return hashlib.sha256(msg.encode("utf-8", errors="replace")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# API publica de entrada
# ---------------------------------------------------------------------------

def check_message(message: str, session_id: str | None = None) -> tuple[bool, str | None, str | None]:
    """Evalua un mensaje contra todas las categorias de defensa.

    Retorna (blocked, category, pattern_excerpt).
      - blocked=True si matchea cualquier regla.
      - category: 'length', 'injection', 'roleplay', 'exfiltration',
                  'prompt_leak', 'encoding', 'syntax' o None.
      - pattern_excerpt: snippet del patron que matcheo (para debugging).

    Loguea cada bloqueo con warning, sin exponer el mensaje completo.
    """
    if not message:
        return False, None, None

    if len(message) > MAX_MESSAGE_LENGTH:
        _log_block("length", "too_long", message, session_id, length=len(message))
        return True, "length", "too_long"

    normalized = _normalize(message)

    for category, patterns in _CATEGORIES:
        for pattern in patterns:
            match = pattern.search(normalized)
            if match:
                excerpt = match.group(0)[:60]
                _log_block(category, excerpt, message, session_id)
                return True, category, excerpt

    return False, None, None


def get_block_message(category: str | None) -> str:
    """Mensaje legible para devolver al usuario cuando se bloquea."""
    if not category:
        return GENERIC_BLOCK_MESSAGE
    return _BLOCK_MESSAGES.get(category, GENERIC_BLOCK_MESSAGE)


# ---------------------------------------------------------------------------
# API publica de salida
# ---------------------------------------------------------------------------

def output_contains_system_prompt(answer: str) -> bool:
    """True si la respuesta del LLM filtra strings que solo existen en el system prompt."""
    if not answer:
        return False
    return any(marker in answer for marker in _SYSTEM_PROMPT_MARKERS)


def output_contains_dangerous_topic(answer: str) -> bool:
    """True si la respuesta menciona actividades ilicitas que indican jailbreak exitoso."""
    if not answer:
        return False
    answer_low = answer.lower()
    return any(term in answer_low for term in _DANGEROUS_OUTPUT_TERMS)


def is_hallucinated_session_leak(answer: str) -> bool:
    """True si la respuesta inventa datos de otros usuarios/sesiones (hallucination)."""
    if not answer:
        return False
    answer_low = answer.lower()
    return any(phrase in answer_low for phrase in _HALLUCINATED_LEAK_PHRASES)


def check_output(answer: str, session_id: str | None = None) -> tuple[bool, str | None]:
    """Evalua la respuesta del LLM. Si es insegura, retorna (True, motivo).

    Cubre: leak del system prompt, topicos peligrosos, hallucination de sesiones.
    """
    if output_contains_system_prompt(answer):
        _log_block("output_system_prompt_leak", "system_prompt_marker", answer, session_id)
        return True, "system_prompt_leak"
    if output_contains_dangerous_topic(answer):
        _log_block("output_dangerous_topic", "dangerous_term", answer, session_id)
        return True, "dangerous_topic"
    if is_hallucinated_session_leak(answer):
        # Solo logueamos como warning, no es necesariamente malicioso
        logger.warning(
            "output_hallucinated_session_leak | session=%s | hash=%s",
            session_id, _redact(answer),
        )
        return True, "hallucinated_session_leak"
    return False, None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log_block(
    category: str,
    pattern: str,
    message: str,
    session_id: str | None,
    **extra,
) -> None:
    """Log estructurado de un bloqueo, sin filtrar contenido sensible."""
    parts = [
        f"security_block",
        f"category={category}",
        f"pattern={pattern!r}",
        f"session={session_id or '-'}",
        f"hash={_redact(message)}",
    ]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.warning(" | ".join(parts))
