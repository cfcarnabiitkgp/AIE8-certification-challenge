"""Configuration management for the application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Keys
    openai_api_key: str
    cohere_api_key: str
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "research_guidelines"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # LLM Configuration
    llm_model: str = "gpt-4o-mini"  # Legacy/default model
    llm_temperature: float = 0.1
    embedding_model: str = "text-embedding-3-small"

    # Agent-specific LLM Models
    clarity_agent_model: str = "gpt-4o-mini"  # Fast, cost-effective for pattern matching
    rigor_agent_model: str = "gpt-4o"  # Powerful model for reasoning about methodology
    orchestrator_model: str = "gpt-4o"  # Quality gate for final validation

    # ==========================================
    # Retriever Configuration
    # ==========================================

    # Global default retriever type (fallback)
    default_retriever_type: str = "naive"

    # Clarity Agent Retriever Configuration
    clarity_agent_retriever_type: str = "naive"
    clarity_agent_retriever_k: int = 6
    clarity_agent_retriever_initial_k: int = 20  # For rerank only

    # Rigor Agent Retriever Configuration
    rigor_agent_retriever_type: str = "naive"
    rigor_agent_retriever_k: int = 6
    rigor_agent_retriever_initial_k: int = 20  # For rerank only

    # Cohere Rerank Configuration (shared across all agents using rerank)
    cohere_rerank_model: str = "rerank-v3.5"
    cohere_rerank_initial_k: int = 20  # Default if not specified per-agent

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()

