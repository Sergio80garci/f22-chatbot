from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider: "ollama" (local), "groq" (cloud), "gemini" (Google)
    llm_provider: str = "ollama"

    # Ollama settings (local dev)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    # Groq settings
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Gemini settings (Google AI Studio — aistudio.google.com)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # HuggingFace embeddings (usado cuando llm_provider=groq, corre en CPU Railway)
    hf_embed_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # ChromaDB
    chroma_path: str = "./data/chroma_db"
    chroma_collection: str = "f22_knowledge_base"
    docs_path: str = "./data/f22/raw"
    processed_path: str = "./data/f22/processed"
    top_k_results: int = 5

    # CORS — lista separada por comas
    # Local:  http://localhost:5173
    # Cloud:  https://tu-app.netlify.app,http://localhost:5173
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
