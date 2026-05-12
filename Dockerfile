FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/chroma_db/ viene en el COPY anterior (pre-generado localmente con Gemini embeddings)
# Para actualizar documentos: re-ingestar localmente y hacer rebuild + redeploy

ENV CHROMA_PATH=/app/data/chroma_db
ENV DOCS_PATH=/app/data/f22/raw
ENV PROCESSED_PATH=/app/data/f22/processed

EXPOSE 8080
CMD ["python", "scripts/start.py"]
