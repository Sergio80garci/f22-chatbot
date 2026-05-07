FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descarga el modelo multilingüe durante el build (queda cacheado en la imagen)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

COPY . .

ENV LLM_PROVIDER=groq
ENV CHROMA_PATH=/app/data/chroma_db
ENV DOCS_PATH=/app/data/f22/raw
ENV PROCESSED_PATH=/app/data/f22/processed

EXPOSE 8080
CMD ["python", "scripts/start.py"]
