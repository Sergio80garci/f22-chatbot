# F22 Chatbot — SII

Sitio web informativo + chatbot RAG sobre el Formulario 22 de Declaración de Renta.
El sistema responde preguntas usando exclusivamente documentos propios. Sin costo de tokens en producción.

## Inicio rápido

```bash
# 1. Copiar configuración
cp .env.example .env

# 2. Agregar documentos F22 en:
#    data/f22/raw/

# 3. Abrir Claude Code en esta carpeta
claude

# 4. Dentro de Claude Code, ejecutar en orden:
/ingest
/build-backend
/build-frontend
/deploy
```

## Requisitos previos

- [Ollama](https://ollama.com) instalado y corriendo
- Python 3.11+
- Node.js 18+
- Tesseract OCR (para procesar imágenes)

## Accesos

| Servicio | URL |
|----------|-----|
| Sitio web | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| Chatbot | http://localhost:5173/chat |
