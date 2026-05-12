FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-spa \
        libgl1 libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-descarga el modelo de embeddings para evitar cold-start lento
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)"

COPY backend ./backend
COPY data/chroma_db ./data/chroma_db
COPY data/summaries_cache.json ./data/summaries_cache.json
COPY data/questions_pool.json ./data/questions_pool.json

ENV PORT=8080 \
    LLM_PROVIDER=groq \
    EMBEDDING_PROVIDER=hf \
    HF_EMBED_MODEL=nomic-ai/nomic-embed-text-v1.5 \
    CHROMA_PATH=/app/data/chroma_db

EXPOSE 8080

CMD exec uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT}
