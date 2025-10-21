"""Tavily search service for retrieving best practices on mathematical and experimental rigor."""
import logging
from typing import Optional
from langchain_core.tools import tool
from tavily import TavilyClient

logger = logging.getLogger(__name__)


class TavilyService:
    """
    Service for searching best practices related to mathematical and experimental rigor.

    This service wraps the Tavily API and provides a LangChain tool for function calling
    that focuses on retrieving authoritative information about:
    - Statistical methods and their appropriate usage
    - Experimental design standards
    - Sample size requirements
    - Mathematical proof techniques
    - Domain-specific research guidelines
    """

    def __init__(self, api_key: str, search_depth: str = "basic", max_results: int = 5):
        """
        Initialize Tavily service.

        Args:
            api_key: Tavily API key
            search_depth: Search depth ("basic" or "advanced")
            max_results: Maximum number of search results to return
        """
        if not api_key:
            raise ValueError("Tavily API key is required")

        self.client = TavilyClient(api_key=api_key)
        self.search_depth = search_depth
        self.max_results = max_results
        logger.info(
            f"Initialized TavilyService with depth={search_depth}, max_results={max_results}"
        )

    def create_search_tool(self):
        """
        Create a LangChain @tool for searching mathematical rigor best practices.

        Returns:
            LangChain tool function decorated with @tool
        """
        # Capture self in closure for access to client settings
        client = self.client
        search_depth = self.search_depth
        max_results = self.max_results

        @tool
        def search_rigor_best_practices(
            query: str,
            domain: Optional[str] = None
        ) -> str:
            """Search for authoritative best practices on mathematical and experimental rigor.

            Use this tool when you need to validate:
            - Domain-specific research standards (e.g., "FDA Phase III trial requirements")
            - Statistical method appropriateness (e.g., "when to use Welch's t-test vs standard t-test")
            - Experimental design standards (e.g., "control group requirements for clinical trials")
            - Sample size requirements (e.g., "minimum sample size for psychology experiments")
            - Multiple testing correction guidelines (e.g., "when to apply Bonferroni correction")
            - Mathematical proof techniques (e.g., "requirements for proving convergence")
            

            Args:
                query: The search query focused on rigor best practices.
                       Examples:
                       - "minimum sample size for randomized controlled trials"
                       - "when to use multiple testing correction"
                       - "control group requirements drug efficacy studies"
                domain: Optional research domain to contextualize the search
                       (e.g., "clinical trials", "machine learning", "psychology")

            Returns:
                Formatted search results with sources and key findings.
            """
            try:
                # Enhance query with domain context if provided
                enhanced_query = query
                if domain:
                    enhanced_query = f"{query} in {domain}"

                logger.info(f"[TavilyService] Searching: {enhanced_query}")

                # Execute Tavily search
                response = client.search(
                    query=enhanced_query,
                    search_depth=search_depth,
                    max_results=max_results,
                    include_answer=True,  # Get AI-generated summary
                    include_raw_content=False  # Just snippets, not full content
                )

                # Format results for LLM consumption
                formatted_result = _format_tavily_response(response)

                logger.info(
                    f"[TavilyService] Found {len(response.get('results', []))} results"
                )
                return formatted_result

            except Exception as e:
                error_msg = f"Tavily search failed: {str(e)}"
                logger.error(f"[TavilyService] {error_msg}")
                return f"Error: {error_msg}. Unable to retrieve external best practices."

        return search_rigor_best_practices


def _format_tavily_response(response: dict) -> str:
    """
    Format Tavily API response for LLM consumption.

    Args:
        response: Raw Tavily API response

    Returns:
        Formatted string with key findings and sources
    """
    parts = []

    # Add AI-generated answer if available (Tavily's summary)
    if response.get("answer"):
        parts.append("=== Summary ===")
        parts.append(response["answer"])
        parts.append("")

    # Add individual search results with sources
    results = response.get("results", [])
    if results:
        parts.append("=== Detailed Sources ===")
        for i, result in enumerate(results[:5], 1):  # Limit to top 5
            parts.append(f"{i}. {result.get('title', 'No title')}")
            parts.append(f"   Source: {result.get('url', 'No URL')}")

            # Add content snippet
            content = result.get("content", "")
            if content:
                # Truncate to 300 chars for brevity
                snippet = content[:300] + "..." if len(content) > 300 else content
                parts.append(f"   {snippet}")
            parts.append("")

    if not parts:
        return "No relevant information found."

    return "\n".join(parts)
