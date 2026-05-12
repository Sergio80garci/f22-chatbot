from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini (desactivado)
    # gemini_api_key: str = ""
    # gemini_model: str = "gemini-2.5-flash"
    # gemini_embedding_model: str = "models/gemini-embedding-001"

    # Groq (LLM)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Ollama (embeddings locales)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"

    # ChromaDB
    chroma_path: str = "./data/chroma_db"
    chroma_collection: str = "f22_knowledge_base"
    docs_path: str = "./data/f22/raw"
    processed_path: str = "./data/f22/processed"
    top_k_results: int = 4

    # CORS — lista separada por comas
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
