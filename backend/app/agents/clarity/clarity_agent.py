"""Clarity analysis agent for technical writing."""
import logging
from typing import Dict, Any, List, Optional
from langchain_core.retrievers import BaseRetriever

from app.agents.base_agent import BaseReviewerAgent
from app.models.schemas import ClarityAnalysisResponse, ClarityReflectionResponse, DocType
from app.prompts.clarity import build_analysis_prompt, build_reflection_prompt

logger = logging.getLogger(__name__)


class ClarityAgent(BaseReviewerAgent):
    """ Agent focused on analyzing writing clarity and readability.

    Checks for:
    - Unclear or ambiguous statements
    - Complex sentence structures
    - Undefined jargon and acronyms
    - Vague references
    - Missing definitions
    """

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        from app.config import settings
        super().__init__(
            agent_name="ClarityAgent",
            agent_description="Analyzes writing clarity and readability",
            model=settings.clarity_agent_model
        )
        self.analysis_prompt = build_analysis_prompt()
        self.reflection_prompt = build_reflection_prompt()
        self.retriever = retriever

    async def analyze(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a section for clarity issues with self-reflection (ReAct pattern).

        Uses structured outputs with Pydantic models for guaranteed data contracts.

        Steps:
        1. Analyze section for clarity issues (structured output)
        2. Self-reflect and validate findings (structured output)
        3. Return validated suggestions

        Args:
            section: Section dictionary with 'title', 'content', 'line_start', 'line_end'

        Returns:
            List of validated clarity suggestion dictionaries
        """

        logger.info("ClarityAgent: analyzing section: %s", section['title'])

        # Step 0: Retrieve relevant clarity guidelines using LangChain retriever (RAG)
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
                        "[ClarityAgent] Retrieved %d relevant guidelines using %s",
                        len(langchain_docs),
                        type(self.retriever).__name__
                    )
                else:
                    logger.info("[ClarityAgent] No relevant guidelines found")
            except Exception as e:
                logger.warning(f"[ClarityAgent] Error retrieving guidelines: {e}")

        # Step 1: Initial analysis with structured output
        analysis_response = await self._invoke_llm_structured(
            self.analysis_prompt,
            ClarityAnalysisResponse,
            section_title=section["title"],
            content=section["content"],
            guidelines_context=guidelines_context
        )

        if not analysis_response or not analysis_response.issues:
            logger.info("[ClarityAgent] No issues found in %s", section['title'])
            return []

        logger.info("[ClarityAgent] Found %d potential issues", len(analysis_response.issues))

        # Step 2: Self-reflection with structured output
        reflection_response = await self._invoke_llm_structured(
            self.reflection_prompt,
            ClarityReflectionResponse,
            section_title=section["title"],
            content=section["content"][:1000],  # Truncate for reflection
            suggestions_count=len(analysis_response.issues)
        )

        if not reflection_response:
            logger.warning("[ClarityAgent] Reflection failed, using original suggestions")
            validated_issues = analysis_response.issues
            reasoning = "Reflection failed, using all original suggestions"
        else:
            validated_issues = reflection_response.validated_suggestions
            reasoning = reflection_response.reasoning
            logger.info("[ClarityAgent] Reflection: %s", reasoning)

        # Step 3: Convert to standardized suggestions
        suggestions = []
        for issue in validated_issues:
            suggestion = self._create_suggestion(
                suggestion_type="clarity",
                severity=issue.severity.value,
                title="Clarity Issue",
                description=issue.issue,
                section=section["title"],
                line_start=section.get("line_start"),
                line_end=section.get("line_end"),
                suggested_fix=issue.suggestion
            )
            suggestions.append(suggestion)

        logger.info("[ClarityAgent] Validated %d suggestions for %s", len(suggestions), section['title'])
        return suggestions
