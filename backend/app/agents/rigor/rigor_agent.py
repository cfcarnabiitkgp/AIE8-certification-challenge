"""Rigor analysis agent for experimental and mathematical soundness."""
from typing import Dict, Any, List, Optional
import logging
from langchain_core.retrievers import BaseRetriever

from app.agents.base_agent import BaseReviewerAgent
from app.models.schemas import RigorAnalysisResponse, RigorReflectionResponse
from app.prompts.rigor import build_analysis_prompt, build_reflection_prompt

logger = logging.getLogger(__name__)


class RigorAgent(BaseReviewerAgent):
    """
    Agent focused on analyzing experimental and mathematical rigor.

    Sample rigor checks include
    - Control experiments before causal claims
    - Statistical test appropriateness
    - Sample sizes and statistical power
    - Confidence intervals, p-values, effect sizes
    - Experimental setup clarity
    - Mathematical assumptions and proofs
    """

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        from app.config import settings
        super().__init__(
            agent_name="RigorAgent",
            agent_description="Analyzes experimental and mathematical rigor",
            model=settings.rigor_agent_model
        )
        self.analysis_prompt = build_analysis_prompt()
        self.reflection_prompt = build_reflection_prompt()
        self.retriever = retriever

    def _is_rigor_relevant(self, section: Dict[str, Any]) -> bool:
        """
        Check if section is relevant for rigor analysis.

        Args:
            section: Section dictionary

        Returns:
            True if section should be analyzed for rigor
        """
        title_lower = section["title"].lower()
        relevant_keywords = [
            "method", "methodology", "experiment", "evaluation",
            "result", "analysis", "proof", "theorem", "lemma",
            "implementation", "setup", "design", "procedure"
        ]
        return any(keyword in title_lower for keyword in relevant_keywords)

    async def analyze(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a section for rigor issues with self-reflection (ReAct pattern).

        Uses structured outputs with Pydantic models for guaranteed data contracts.

        Steps:
        1. Check if section requires rigor analysis
        2. Analyze section for rigor issues (structured output)
        3. Self-reflect and validate findings (structured output)
        4. Return validated suggestions

        Args:
            section: Section dictionary with 'title', 'content', 'line_start', 'line_end'

        Returns:
            List of validated rigor suggestion dictionaries
        """
        # Step 1: Skip if not relevant
        if not self._is_rigor_relevant(section):
            logger.debug("[RigorAgent] Skipping non-relevant section: %s", section['title'])
            return []

        logger.info("[RigorAgent] Analyzing section: %s", section['title'])

        # Step 1.5: Retrieve relevant rigor guidelines using LangChain retriever (RAG)
        guidelines_context = ""
        if self.retriever:
            try:
                # Use first 500 chars of section content as query
                query_text = section["content"][:500] if len(section["content"]) > 500 else section["content"]

                # Use LangChain's ainvoke method for async retrieval
                langchain_docs = await self.retriever.ainvoke(query_text)

                if langchain_docs:
                    # Convert LangChain Documents to context string
                    guidelines_list = [
                        f"- {doc.page_content[:200]}..."
                        if len(doc.page_content) > 200
                        else f"- {doc.page_content}"
                        for doc in langchain_docs
                    ]
                    guidelines_context = "\n".join(guidelines_list)
                    logger.info(
                        "[RigorAgent] Retrieved %d relevant guidelines using %s",
                        len(langchain_docs),
                        type(self.retriever).__name__
                    )
                else:
                    logger.info("[RigorAgent] No relevant guidelines found")
            except Exception as e:
                logger.warning(f"[RigorAgent] Error retrieving guidelines: {e}")

        # Step 2: Initial analysis with structured output
        analysis_response = await self._invoke_llm_structured(
            self.analysis_prompt,
            RigorAnalysisResponse,
            section_title=section["title"],
            content=section["content"],
            guidelines_context=guidelines_context
        )

        if not analysis_response or not analysis_response.issues:
            logger.info("[RigorAgent] No issues found in %s", section['title'])
            return []

        logger.info("[RigorAgent] Found %d potential issues", len(analysis_response.issues))

        # Step 3: Self-reflection with structured output
        reflection_response = await self._invoke_llm_structured(
            self.reflection_prompt,
            RigorReflectionResponse,
            section_title=section["title"],
            content=section["content"][:1000],  # Truncate for reflection
            suggestions_count=len(analysis_response.issues)
        )

        if not reflection_response:
            logger.warning("[RigorAgent] Reflection failed, using original suggestions")
            validated_issues = analysis_response.issues
            reasoning = "Reflection failed, using all original suggestions"
        else:
            validated_issues = reflection_response.validated_suggestions
            reasoning = reflection_response.reasoning
            logger.info("[RigorAgent] Reflection: %s", reasoning)

        # Step 4: Convert to standardized suggestions
        suggestions = []
        for issue in validated_issues:
            suggestion = self._create_suggestion(
                suggestion_type="rigor",
                severity=issue.severity.value,
                title="Rigor Issue",
                description=issue.issue,
                section=section["title"],
                line_start=section.get("line_start"),
                line_end=section.get("line_end"),
                suggested_fix=issue.suggestion
            )
            suggestions.append(suggestion)

        logger.info("[RigorAgent] Validated %d suggestions for %s", len(suggestions), section['title'])
        return suggestions
