"""BM25 retriever builder using LangChain's BM25Retriever."""
from typing import Dict, Any, List, Union
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
import logging

from app.retrievers.builder import RetrieverBuilder
from app.retrievers.registry import RetrieverRegistry
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

logger = logging.getLogger(__name__)


@RetrieverRegistry.register("bm25")
class BM25RetrieverBuilder(RetrieverBuilder):
    """
    Builder for BM25 retriever.

    This builder creates a BM25Retriever that uses traditional keyword-based
    retrieval with BM25 scoring algorithm. Unlike semantic search, BM25 relies
    on term frequency and document length normalization.

    BM25 is particularly effective for:
    - Exact term matching
    - Queries with specific technical terms or jargon
    - Short, keyword-focused queries

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
        Build a BM25Retriever.

        This retriever needs to load all documents from the vector store
        to build its BM25 index. The documents are filtered by doc_type if specified.

        Args:
            vector_store: VectorStoreService instance
            config: Configuration dictionary

        Returns:
            BM25Retriever instance
        """
        logger.info(
            f"Building BM25 retriever with k={config['k']}, "
            f"doc_type={config.get('doc_type')}"
        )

        # Retrieve all documents for BM25 indexing
        # BM25Retriever needs the full corpus to calculate term statistics
        import asyncio
        import nest_asyncio

        # Allow nested event loops
        nest_asyncio.apply()

        # Fetch all documents with optional doc_type filter
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        documents = loop.run_until_complete(
            vector_store.get_all_documents(doc_type=config.get("doc_type"))
        )

        if not documents:
            logger.warning(
                f"No documents found for BM25 retriever "
                f"(doc_type={config.get('doc_type')}). "
                f"Retriever will return empty results."
            )
            # Create an empty retriever - it won't return results but won't crash
            documents = [Document(page_content="", metadata={})]

        logger.info(f"Loaded {len(documents)} documents for BM25 indexing")

        # Create BM25Retriever
        retriever = BM25Retriever.from_documents(
            documents=documents,
            k=config["k"]
        )

        return retriever

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
