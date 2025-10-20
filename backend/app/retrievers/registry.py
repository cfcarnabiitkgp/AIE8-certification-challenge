"""Registry pattern for retriever builders."""
from typing import Dict, Type, List
from langchain_core.retrievers import BaseRetriever
import logging

from app.services.vector_store import VectorStoreService
from app.retrievers.builder import RetrieverBuilder

logger = logging.getLogger(__name__)


class RetrieverRegistry:
    """
    Registry for retriever builders using singleton pattern.

    This registry allows registration of retriever builders and creation of retrievers
    without if-else blocks. New retriever types can be added by simply decorating
    a builder class with @RetrieverRegistry.register("type_name").

    Example:
        @RetrieverRegistry.register("my_retriever")
        class MyRetrieverBuilder(RetrieverBuilder):
            def build(self, vector_store, config):
                return MyRetriever(...)

            def validate_config(self, config):
                if "required_field" not in config:
                    raise ValueError("required_field is missing")

        # Later, create the retriever
        retriever = RetrieverRegistry.create(
            "my_retriever",
            vector_store,
            {"required_field": "value"}
        )
    """

    _instance = None
    _builders: Dict[str, Type[RetrieverBuilder]] = {}

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, retriever_type: str):
        """
        Decorator to register a retriever builder.

        Usage:
            @RetrieverRegistry.register("my_retriever")
            class MyRetrieverBuilder(RetrieverBuilder):
                ...

        Args:
            retriever_type: Unique identifier for this retriever type

        Returns:
            Decorator function that registers the builder class
        """
        def decorator(builder_class: Type[RetrieverBuilder]):
            if retriever_type in cls._builders:
                logger.warning(
                    f"Retriever type '{retriever_type}' already registered. Overwriting."
                )
            cls._builders[retriever_type] = builder_class
            logger.info(f"Registered retriever type: {retriever_type}")
            return builder_class
        return decorator

    @classmethod
    def create(
        cls,
        retriever_type: str,
        vector_store: VectorStoreService,
        config: Dict[str, any] = None
    ) -> BaseRetriever:
        """
        Create a retriever instance.

        This method looks up the appropriate builder for the given retriever type,
        validates the configuration, and builds the retriever.

        Args:
            retriever_type: Type of retriever to create (must be registered)
            vector_store: VectorStoreService instance
            config: Optional configuration dictionary (merged with defaults)

        Returns:
            LangChain BaseRetriever instance

        Raises:
            ValueError: If retriever type is not registered or configuration is invalid
        """
        if retriever_type not in cls._builders:
            available = ", ".join(cls._builders.keys()) if cls._builders else "none"
            raise ValueError(
                f"Unknown retriever type: '{retriever_type}'. "
                f"Available types: {available}"
            )

        builder_class = cls._builders[retriever_type]
        builder = builder_class()

        # Merge with defaults
        final_config = {**builder.get_default_config(), **(config or {})}

        # Validate config
        builder.validate_config(final_config)

        # Build retriever
        logger.info(
            f"Creating retriever: {retriever_type} with config: "
            f"{cls._sanitize_config_for_logging(final_config)}"
        )
        return builder.build(vector_store, final_config)

    @classmethod
    def list_available(cls) -> List[str]:
        """
        Return list of registered retriever types.

        Returns:
            List of retriever type names
        """
        return list(cls._builders.keys())

    @classmethod
    def is_registered(cls, retriever_type: str) -> bool:
        """
        Check if a retriever type is registered.

        Args:
            retriever_type: Retriever type to check

        Returns:
            True if registered, False otherwise
        """
        return retriever_type in cls._builders

    @classmethod
    def _sanitize_config_for_logging(cls, config: Dict[str, any]) -> Dict[str, any]:
        """
        Sanitize config for logging (hide sensitive values).

        Args:
            config: Configuration dictionary

        Returns:
            Sanitized configuration dictionary
        """
        sanitized = config.copy()
        sensitive_keys = ["cohere_api_key", "api_key", "password", "token"]

        for key in sensitive_keys:
            if key in sanitized and sanitized[key]:
                sanitized[key] = "***REDACTED***"

        return sanitized
