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
    tavily_api_key: str = ""  # Optional: leave empty to disable Tavily

    # LangChain/LangSmith Configuration (optional - for evaluation tracing)
    langchain_api_key: str = ""  # Optional: for LangSmith tracing
    
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
    embedding_model: str = "text-embedding-3-large"

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
    clarity_agent_retriever_type: str = "naive" # "cohere_rerank", "naive"
    clarity_agent_retriever_k: int = 8
    clarity_agent_retriever_initial_k: int = 20  # For rerank only

    # Rigor Agent Retriever Configuration
    rigor_agent_retriever_type: str = "naive" # "cohere_rerank", "naive"
    rigor_agent_retriever_k: int = 8
    rigor_agent_retriever_initial_k:1 int = 20  # For rerank only

    # Cohere Rerank Configuration (shared across all agents using rerank)
    cohere_rerank_model: str = "rerank-v3.5"
    cohere_rerank_initial_k: int = 20  # Default if not specified per-agent

    # ==========================================
    # Tavily Configuration (for Rigor Agent)
    # ==========================================
    rigor_agent_enable_tavily: bool = True  # Feature flag for Tavily search
    tavily_search_depth: str = "basic"  # "basic" or "advanced"
    tavily_max_results: int = 5  # Maximum search results to return
    tavily_max_calls_per_section: int = 2  # Maximum tool calls per section (rate limiting)

    # ==========================================
    # Document Chunking Configuration
    # ==========================================
    chunking_strategy: str = "semantic"  # "fixed" or "semantic"

    # Fixed-size chunking parameters (used when chunking_strategy="fixed")
    fixed_chunk_size: int = 1000
    fixed_chunk_overlap: int = 200

    # Semantic chunking parameters (used when chunking_strategy="semantic")
    semantic_breakpoint_threshold_type: str = "percentile"  # "percentile", "standard_deviation", "interquartile"
    semantic_breakpoint_threshold_amount: float = 95  # For percentile: 95th percentile
    semantic_min_chunk_size: int = 100  # Minimum chunk size in characters
    semantic_max_chunk_size: int = 2000  # Maximum chunk size in characters

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_tavily_enabled(self) -> bool:
        """Check if Tavily is enabled and API key is provided."""
        return self.rigor_agent_enable_tavily and bool(self.tavily_api_key)

settings = Settings()