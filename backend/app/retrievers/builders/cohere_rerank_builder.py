"""Cohere rerank retriever builder using contextual compression."""
import logging
from typing import Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

from app.retrievers.builder import RetrieverBuilder
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.qdrant_retriever import QdrantRetriever
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

logger = logging.getLogger(__name__)


@RetrieverRegistry.register("cohere_rerank")
class CohereRerankRetrieverBuilder(RetrieverBuilder):
    """
    Builder for Cohere rerank retriever.

    This builder creates a two-stage retrieval pipeline:
    1. Initial retrieval: Fetch a larger set of candidate documents from Qdrant
    2. Reranking: Use Cohere's rerank API to reorder candidates by relevance

    The final output is the top-k documents after reranking.

    Configuration:
        k: Number of final documents to return (default: 5)
        initial_k: Number of candidates to retrieve before reranking (default: 20)
        model: Cohere rerank model name (default: from settings)
        cohere_api_key: Cohere API key (required)
        doc_type: Optional document type filter (CLARITY, RIGOR, INTEGRITY, GENERAL)
    """

    def build(
        self,
        vector_store: VectorStoreService,
        config: Dict[str, Any]
    ) -> BaseRetriever:
        """
        Build a ContextualCompressionRetriever with CohereRerank.

        Args:
            vector_store: VectorStoreService instance
            config: Configuration dictionary

        Returns:
            ContextualCompressionRetriever instance
        """
        logger.info(
            f"Building Cohere rerank retriever with k={config['k']}, "
            f"initial_k={config['initial_k']}, model={config['model']}, "
            f"doc_type={config.get('doc_type')}"
        )

        # Stage 1: Base retriever (get more candidates)
        base_retriever = QdrantRetriever(
            vector_store=vector_store,
            k=config["initial_k"],
            doc_type=config.get("doc_type")
        )

        # Stage 2: Rerank compressor
        compressor = CohereRerank(
            model=config["model"],
            cohere_api_key=config["cohere_api_key"],
            top_n=config["k"]  # Return top k after reranking
        )

        # Combine into ContextualCompressionRetriever
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required fields
        required_fields = ["k", "initial_k", "model", "cohere_api_key"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"'{field}' is required in config")

        # Validate k
        if not isinstance(config["k"], int) or config["k"] <= 0:
            raise ValueError("'k' must be a positive integer")

        # Validate initial_k
        if not isinstance(config["initial_k"], int) or config["initial_k"] <= 0:
            raise ValueError("'initial_k' must be a positive integer")

        # Check that initial_k >= k
        if config["initial_k"] < config["k"]:
            raise ValueError(
                f"'initial_k' ({config['initial_k']}) must be >= 'k' ({config['k']}). "
                f"Cannot return more documents than retrieved."
            )

        # Validate API key
        if not config["cohere_api_key"]:
            raise ValueError(
                "'cohere_api_key' cannot be empty. "
                "Please set COHERE_API_KEY in your environment or config."
            )

        # Validate model name
        if not isinstance(config["model"], str) or not config["model"]:
            raise ValueError("'model' must be a non-empty string")

        # Validate doc_type
        if "doc_type" in config and config["doc_type"] is not None:
            if not isinstance(config["doc_type"], DocType):
                raise ValueError(
                    f"'doc_type' must be a DocType enum or None, "
                    f"got {type(config['doc_type'])}"
                )

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default configuration.

        Returns:
            Default configuration dictionary
        """
        from app.config import settings

        return {
            "k": 10,
            "initial_k": settings.cohere_rerank_initial_k if hasattr(settings, 'cohere_rerank_initial_k') else 20,
            "model": settings.cohere_rerank_model if hasattr(settings, 'cohere_rerank_model') else "rerank-v3.5",
            "cohere_api_key": settings.cohere_api_key if hasattr(settings, 'cohere_api_key') else "",
            "doc_type": None
        }
