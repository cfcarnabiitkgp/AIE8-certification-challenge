"""Naive retriever builder using direct Qdrant similarity search."""
from typing import Dict, Any
from langchain_core.retrievers import BaseRetriever
import logging

from app.retrievers.builder import RetrieverBuilder
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.qdrant_retriever import QdrantRetriever
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

logger = logging.getLogger(__name__)


@RetrieverRegistry.register("naive")
class NaiveRetrieverBuilder(RetrieverBuilder):
    """
    Builder for naive Qdrant retriever.

    This builder creates a simple QdrantRetriever that performs direct
    similarity search using cosine distance without any reranking or
    additional processing.

    Configuration:
        k: Number of documents to retrieve (default: 5)
        doc_type: Optional document type filter (CLARITY, RIGOR, INTEGRITY, GENERAL)
    """

    def build(
        self,
        vector_store: VectorStoreService,
        config: Dict[str, Any]
    ) -> BaseRetriever:
        """
        Build a QdrantRetriever.

        Args:
            vector_store: VectorStoreService instance
            config: Configuration dictionary

        Returns:
            QdrantRetriever instance
        """
        logger.info(
            f"Building naive retriever with k={config['k']}, "
            f"doc_type={config.get('doc_type')}"
        )

        return QdrantRetriever(
            vector_store=vector_store,
            k=config["k"],
            doc_type=config.get("doc_type")
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Check k parameter
        if "k" not in config:
            raise ValueError("'k' is required in config")

        if not isinstance(config["k"], int) or config["k"] <= 0:
            raise ValueError("'k' must be a positive integer")

        # Check doc_type parameter
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
        return {
            "k": 10,
            "doc_type": None
        }
