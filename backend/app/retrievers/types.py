"""Type definitions for retrievers."""
from typing import TypedDict, Literal, Optional, Any, Dict
from app.models.schemas import DocType

RetrieverType = Literal["naive", "cohere_rerank"]


class BaseRetrieverConfig(TypedDict, total=False):
    """Base configuration for all retrievers."""
    k: int  # Number of documents to return
    doc_type: Optional[DocType]  # Filter by document type


class NaiveRetrieverConfig(BaseRetrieverConfig):
    """Configuration for naive retriever."""
    pass  # Uses only base config


class CohereRerankConfig(BaseRetrieverConfig):
    """Configuration for Cohere rerank retriever."""
    initial_k: int  # Candidates before reranking
    model: str  # Cohere rerank model
    cohere_api_key: str  # API key


# Union type for all configs (flexible for extension)
RetrieverConfig = Dict[str, Any]
