from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini (desactivado)
    # gemini_api_key: str = ""
    # gemini_model: str = "gemini-2.5-flash"
    # gemini_embedding_model: str = "models/gemini-embedding-001"

    # LLM provider: "groq" (cloud, rápido pero con TPD) o "ollama" (local, lento pero ilimitado)
    llm_provider: str = "groq"

    # Groq (LLM cloud)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Ollama (embeddings locales + LLM local opcional)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.1:8b"

    # ChromaDB
    chroma_path: str = "./data/chroma_db"
    chroma_collection: str = "f22_knowledge_base"
    docs_path: str = "./data/f22/raw"
    processed_path: str = "./data/f22/processed"
    top_k_results: int = 3
    llm_max_tokens: int = 1024

    # CORS — lista separada por comas
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
