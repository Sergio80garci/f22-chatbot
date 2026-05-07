# F22 Chatbot — SII Proyecto

## Objetivo
Construir un sistema RAG (Retrieval-Augmented Generation) compuesto por:
1. **Sitio web informativo** sobre el Formulario F22 (Declaración de Renta)
2. **Chatbot integrado** que responde preguntas usando SOLO los documentos del cuaderno F22

El sistema NO se conecta a NotebookLM. Los documentos exportados se procesan localmente.
El chatbot en producción usa Ollama como LLM — NO gasta tokens de Claude/Anthropic.

---

## Stack Tecnológico

| Capa | Herramienta | Versión |
|------|-------------|---------|
| LLM (producción) | Ollama + Llama 3.2 | latest |
| Embeddings | nomic-embed-text (via Ollama) | latest |
| Vector DB | ChromaDB | >= 0.5 |
| OCR (imágenes) | Tesseract + pytesseract | >= 5.0 |
| Backend | FastAPI + LangChain | Python 3.11+ |
| Frontend | React + Vite | Node 18+ |
| Orquestación | LangChain | >= 0.2 |
| Contenedores | Docker + docker-compose | latest |

---

## Estructura de Carpetas

```
f22-chatbot/
├── CLAUDE.md                        ← este archivo
├── .claude/
│   └── commands/                    ← todos los comandos Claude Code (/nombre)
│       ├── ingest.md                ← /ingest
│       ├── build-backend.md         ← /build-backend
│       ├── build-frontend.md        ← /build-frontend
│       ├── deploy.md                ← /deploy
│       ├── security-audit.md        ← /security-audit
│       ├── responsive-design.md     ← /responsive-design
│       └── chat-ui-centrado.md      ← /chat-ui-centrado
├── data/
│   └── f22/
│       ├── raw/                     ← documentos originales aquí
│       └── processed/               ← texto extraído (autogenerado)
├── backend/
│   ├── ingest/
│   │   ├── extract.py               ← extrae texto de PDF/Word/Excel/IMG
│   │   ├── chunker.py               ← divide texto en chunks semánticos
│   │   └── embedder.py              ← genera embeddings y guarda en ChromaDB
│   ├── rag/
│   │   ├── vectorstore.py           ← conexión y manejo de ChromaDB
│   │   ├── retriever.py             ← búsqueda semántica top-K
│   │   └── pipeline.py             ← orquesta RAG completo con LangChain
│   ├── api/
│   │   ├── main.py                  ← FastAPI app principal
│   │   ├── routes/
│   │   │   ├── chat.py              ← POST /chat
│   │   │   └── documents.py         ← GET /documents (lista fuentes)
│   │   └── models.py               ← Pydantic schemas
│   └── config.py                    ← variables de entorno y configuración
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx             ← sitio informativo F22
│   │   │   ├── Chat.jsx             ← chatbot integrado
│   │   │   └── Documentos.jsx       ← visor de fuentes citadas
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── SourcePanel.jsx      ← muestra qué parte del F22 respondió
│   │   │   └── Navbar.jsx
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── ingest_documents.py          ← ejecuta ingestión completa
│   └── evaluate_rag.py             ← prueba calidad de respuestas
├── .env.example
├── .env                             ← NO subir a git
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

---

## Reglas Importantes

1. **NUNCA usar la API de Anthropic para inferencia en producción** — solo Ollama local
2. **NUNCA subir .env a git** — contiene rutas sensibles
3. **Todos los documentos fuente** están en `data/f22/raw/` — no modificar manualmente
4. **Cada respuesta del chatbot DEBE incluir** la fuente exacta (nombre del archivo + página/sección)
5. **El chunking** debe respetar la estructura del F22: secciones, códigos de línea, instrucciones
6. **OCR obligatorio** para archivos de imagen — usar Tesseract con idioma español (`spa`)
7. **Estilo visual** del sitio web debe seguir identidad SII: azul #0B4C8C, naranja #E8593C, tipografía limpia

---

## Configuración Ollama (debe estar corriendo antes de iniciar)

```bash
# Instalar modelos necesarios (solo una vez)
ollama pull llama3.2
ollama pull nomic-embed-text

# Verificar que está corriendo
ollama list
```

Variables de entorno en `.env`:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
CHROMA_PATH=./data/chroma_db
DOCS_PATH=./data/f22/raw
PROCESSED_PATH=./data/f22/processed
```

---

## Comandos Frecuentes

```bash
# 1. Procesar documentos F22 (primera vez o cuando agregues docs nuevos)
python scripts/ingest_documents.py

# 2. Levantar backend
uvicorn backend.api.main:app --reload --port 8000

# 3. Levantar frontend
cd frontend && npm run dev

# 4. Todo con Docker
docker-compose up --build

# 5. Evaluar calidad RAG
python scripts/evaluate_rag.py
```

---

## Contexto del Dominio F22

El Formulario 22 es la **Declaración Anual de Impuesto a la Renta** en Chile, administrado por el SII.
- Contiene secciones numeradas con códigos de línea (ej: línea 1, código 159)
- Incluye instrucciones detalladas, ejemplos y tablas de referencia
- El chatbot debe entender terminología tributaria chilena
- Las respuestas deben ser precisas y citar la sección exacta del formulario

---

## Comandos Claude Code disponibles

### Flujo principal (ejecutar en orden)

| Comando | Descripción |
|---------|-------------|
| `/ingest` | Procesa todos los documentos de `data/f22/raw/` y los carga en ChromaDB |
| `/build-backend` | Construye FastAPI + pipeline RAG completo con LangChain y Ollama |
| `/build-frontend` | Construye sitio React con estilo SII + chatbot integrado |
| `/deploy` | Levanta backend + frontend con Docker Compose |

### Mantenimiento y mejoras

| Comando | Descripción |
|---------|-------------|
| `/security-audit` | Auditoría de seguridad completa del sistema |
| `/responsive-design` | Guía para hacer cualquier componente React completamente responsive |
| `/chat-ui-centrado` | Corregir chat que se deforma en pantallas grandes + skeleton + preguntas aleatorias |
