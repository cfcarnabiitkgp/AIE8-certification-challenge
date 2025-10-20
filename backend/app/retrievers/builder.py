"""Abstract builder for creating retrievers."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_core.retrievers import BaseRetriever

from app.services.vector_store import VectorStoreService


class RetrieverBuilder(ABC):
    """
    Abstract builder for creating retrievers.

    This class defines the interface that all retriever builders must implement.
    Each concrete builder is responsible for:
    1. Validating its specific configuration
    2. Building a retriever instance from the configuration
    3. Providing default configuration values
    """

    @abstractmethod
    def build(
        self,
        vector_store: VectorStoreService,
        config: Dict[str, Any]
    ) -> BaseRetriever:
        """
        Build a retriever instance.

        Args:
            vector_store: VectorStoreService instance for accessing the vector database
            config: Configuration dictionary containing retriever-specific parameters

        Returns:
            LangChain BaseRetriever instance

        Raises:
            ValueError: If configuration is invalid or required dependencies are missing
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration before building.

        This method should check that all required fields are present and have
        valid values. It should raise ValueError with a descriptive message if
        validation fails.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default configuration for this retriever.

        Override this method to provide sensible defaults for your retriever.
        These defaults will be merged with user-provided configuration.

        Returns:
            Dictionary containing default configuration values
        """
        return {
            "k": 5,
            "doc_type": None
        }
