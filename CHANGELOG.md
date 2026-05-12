# Changelog — F22 Chatbot SII

## [2.1.0] — 2026-05-12
### Backend
- Migración de Gemini API a Groq (llama-3.1-8b-instant) para LLM
- Migración de Gemini Embeddings a Ollama (nomic-embed-text) para embeddings
- Cache de resúmenes persistido en `data/summaries_cache.json`
- Pool de preguntas sugeridas persistido en `data/questions_pool.json`
- Script `generate_summaries.py` para pre-generar resúmenes sin costo
- Script `generate_questions.py` para pre-generar 228 preguntas (3 por documento)
- Endpoint `/api/version` con información de versión y stack
- Preguntas relacionadas contextualizadas con pregunta + respuesta (70/30)

### Frontend
- Eliminada sección TODIO del menú y rutas
- Nuevo logo SII en navbar (Servicio de Impuestos Internos)
- Footer con versión de frontend y backend
- Polling en /documentos para cargar resúmenes progresivamente

## [2.0.0] — 2026-05-07
### Backend
- Migración de Ollama a Gemini API (gemini-2.5-flash + gemini-embedding-001)
- Re-ingestión de 76 documentos F22 con 854 chunks en ChromaDB
- FastAPI BackgroundTasks para generación asíncrona de resúmenes

### Frontend
- Chat con streaming SSE
- Página de documentos con resúmenes generados por IA
- Preguntas sugeridas dinámicas
- Diseño responsive con identidad SII

## [1.0.0] — 2026-04-01
### Inicial
- Stack: Ollama (llama3.2 + nomic-embed-text) + ChromaDB + FastAPI + React
- Ingestión de documentos PDF, DOCX, XLSX con OCR
- Pipeline RAG con LangChain
