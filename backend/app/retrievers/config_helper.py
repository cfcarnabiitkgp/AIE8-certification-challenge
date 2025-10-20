"""Helper to build retriever configurations from settings."""
from typing import Dict, Any, Optional
import logging

from app.models.schemas import DocType

logger = logging.getLogger(__name__)


class RetrieverConfigHelper:
    """
    Helper to build retriever configurations from settings.

    This class provides utility methods to extract retriever configuration
    from the application settings on a per-agent basis.
    """

    @staticmethod
    def get_agent_retriever_config(
        agent_name: str,
        doc_type: Optional[DocType] = None
    ) -> Dict[str, Any]:
        """
        Get retriever configuration for a specific agent.

        This method reads the per-agent retriever settings from the application
        configuration and builds a complete configuration dictionary.

        Args:
            agent_name: Agent name (e.g., "clarity", "rigor", "integrity")
            doc_type: Optional document type filter

        Returns:
            Configuration dictionary suitable for RetrieverRegistry.create()

        Example:
            >>> config = RetrieverConfigHelper.get_agent_retriever_config("clarity", DocType.CLARITY)
            >>> retriever = RetrieverRegistry.create("naive", vector_store, config)
        """
        from app.config import settings

        agent_name_lower = agent_name.lower()

        # Get retriever type for this agent
        retriever_type = RetrieverConfigHelper.get_agent_retriever_type(agent_name)

        # Build base config
        k_key = f"{agent_name_lower}_agent_retriever_k"
        k = getattr(settings, k_key, 5)

        config = {
            "k": k,
            "doc_type": doc_type
        }

        # Add retriever-specific config
        if retriever_type == "cohere_rerank":
            initial_k_key = f"{agent_name_lower}_agent_retriever_initial_k"
            initial_k = getattr(settings, initial_k_key, settings.cohere_rerank_initial_k)

            config.update({
                "initial_k": initial_k,
                "model": settings.cohere_rerank_model,
                "cohere_api_key": settings.cohere_api_key
            })

        logger.debug(
            f"Built config for {agent_name} agent: retriever_type={retriever_type}, "
            f"k={config['k']}, doc_type={doc_type}"
        )

        return config

    @staticmethod
    def get_agent_retriever_type(agent_name: str) -> str:
        """
        Get retriever type for a specific agent.

        Args:
            agent_name: Agent name (e.g., "clarity", "rigor", "integrity")

        Returns:
            Retriever type string (e.g., "naive", "cohere_rerank")
        """
        from app.config import settings

        agent_name_lower = agent_name.lower()
        retriever_type_key = f"{agent_name_lower}_agent_retriever_type"

        retriever_type = getattr(
            settings,
            retriever_type_key,
            settings.default_retriever_type
        )

        logger.debug(f"Retriever type for {agent_name} agent: {retriever_type}")

        return retriever_type
